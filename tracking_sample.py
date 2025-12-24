import tkinter as tk
from tkinter import messagebox, Tk
from tkinter import ttk
import os
import pandas as pd
from datetime import datetime
from PIL import Image, ImageTk
import cv2
import sys
import win32event
import win32api
import winerror
import shutil

# ===== SINGLE INSTANCE CHECK =====
mutex = win32event.CreateMutex(None, False, "FQC_SAMPLE_TRACKER_MUTEX")

if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
    root = Tk()
    root.withdraw()
    messagebox.showerror(
        "Aplikasi sudah berjalan",
        "Aplikasi ini sudah terbuka.\nSilakan cek di taskbar atau system tray."
    )
    sys.exit(0)

class SearchableDropdown(tk.Frame):
    def __init__(self, master, values, on_select=None, width=20):
        super().__init__(master)

        self.values = values
        self.on_select = on_select

        # VAR
        self.var = tk.StringVar()

        # ENTRY
        self.entry = tk.Entry(self, textvariable=self.var, width=width)
        self.entry.grid(row=0, column=0, sticky="w")
        self.entry.bind("<KeyRelease>", self._filter_event)
        self.entry.bind("<FocusOut>", self._hide_listbox)

        # BUTTON ▼
        self.btn = tk.Button(self, text="▼", width=1, command=self._toggle_listbox)
        self.btn.grid(row=0, column=1, sticky="e")

        # LISTBOX (hidden initially)
        self.listbox = None

    # ---------------- LISTBOX CONTROL ----------------
    def _toggle_listbox(self):
        if self.listbox:
            self._hide_listbox()
        else:
            self._show_listbox()
            self._update_listbox(self.values)

    def _show_listbox(self):
        if self.listbox:
            return

        self.listbox = tk.Listbox(self, width=self.entry["width"], height=6)
        self.listbox.grid(row=1, column=0, columnspan=2)
        self.listbox.bind("<<ListboxSelect>>", self._choose)
        self.listbox.bind("<Button-1>", self._choose)

    def _hide_listbox(self, event=None):
        if self.listbox:
            self.listbox.destroy()
            self.listbox = None

    # ---------------- FILTERING ----------------
    def _filter_event(self, event):
        typed = self.var.get().lower()

        filtered = [v for v in self.values if typed in v.lower()]

        if not filtered:
            self._hide_listbox()
            return

        self._show_listbox()
        self._update_listbox(filtered)

    def _update_listbox(self, data):
        if not self.listbox:
            return
        self.listbox.delete(0, tk.END)
        for item in data:
            self.listbox.insert(tk.END, item)

    # ---------------- CHOOSE ITEM ----------------
    def _choose(self, event):
        if not self.listbox:
            return

        try:
            idx = self.listbox.curselection()[0]
        except:
            return

        value = self.listbox.get(idx)
        self.var.set(value)
        self._hide_listbox()

        if self.on_select:
            self.on_select(value)

    # ---------------- PUBLIC API ----------------
    def get(self):
        return self.var.get()

    def set(self, value):
        self.var.set(value)


# =============================
# Setup Folder & File
# =============================
if getattr(sys, 'frozen', False):
    # sedang dijalankan sebagai .exe
    base_dir = os.path.dirname(sys.executable)
else:
    # sedang dijalankan sebagai script python biasa
    base_dir = os.path.dirname(os.path.abspath(__file__))
foto_dir = os.path.join(base_dir, "foto")
excel_file = os.path.join(base_dir, "record_peminjaman.xlsx")
    # Load list Item# & Sample
list_file = os.path.join(base_dir, "item_list.xlsx")

xls = pd.ExcelFile(list_file)
# Sheet ITEM
df_item = pd.read_excel(xls, "item_list")
df_item["DropdownText"] = df_item["Item#"].astype(str) + " (" + df_item["NamaSingkat"].astype(str) + ")"

# Sheet NAME
df_name = pd.read_excel(xls, "name_list")
name_values = df_name["Name"].astype(str).tolist()
# dept_values = df_name["Department"].astype(str).tolist()



if not os.path.exists(foto_dir):
    os.makedirs(foto_dir)

if not os.path.exists(excel_file):
    df = pd.DataFrame(columns=[
        "ID","Nama","Department","Sample","Item#","Tanggal_Pinjam",
        "Tanggal_Kembali","Foto_Pinjam","Foto_Kembali",
        "Nama_Kembali","Department_Kembali","Sample_Kembali","Item#_Kembali","Status"])
    df.to_excel(excel_file, index=False)

# =============================
# Fungsi Generate ID
# =============================
def generate_new_id():
    df = pd.read_excel(excel_file)
    if df.empty:
        return "ID0001"
    last_id = df["ID"].str.replace("ID", "").astype(int).max()
    next_id = last_id + 1
    return f"ID{next_id:04d}"

# =============================
# Fungsi Ambil Foto
# =============================
def ambil_foto(path_output):
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        messagebox.showerror("Error", "Kamera tidak dapat dibuka!")
        return False
    cv2.namedWindow("Ambil Foto")
    while True:
        ret, frame = cap.read()
        if not ret:
            messagebox.showerror("Error", "Gagal membaca frame kamera!")
            break
        cv2.imshow("Ambil Foto", frame)
        key = cv2.waitKey(1)
        if key == 32:  # SPACE capture
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
            font = cv2.FONT_HERSHEY_SIMPLEX
            scale, thickness = 0.7, 2
            (w, h), _ = cv2.getTextSize(timestamp, font, scale, thickness)
            x, y = frame.shape[1]-w-10, frame.shape[0]-10
            cv2.putText(frame, timestamp, (x, y), font, scale, (255,255,255), thickness, cv2.LINE_AA)
            cv2.imwrite(path_output, frame)
            break
        if key == 27:  # ESC cancel
            cap.release()
            cv2.destroyAllWindows()
            return False
    cap.release()
    cv2.destroyAllWindows()
    return os.path.exists(path_output)

# =============================
# Fungsi Refresh List ID Aktif
# =============================
def refresh_list_id():
    listbox_id.delete(0, tk.END)
    df = pd.read_excel(excel_file)
    aktif = df[df["Status"]=="Dipinjam"]
    for _, row in aktif.iterrows():
        listbox_id.insert(tk.END, f"{row['ID']} ({row['Sample']})")

# =============================
# Fungsi Preview Foto + Data
# =============================
def preview_data(new_id, nama, dept, sample, item, foto_path, is_pinjam=True):
    win = tk.Toplevel(root)
    win.title("Preview Data")
    win.geometry("400x500")
    txt = f"ID: {new_id}\nNama: {nama}\nDepartment: {dept}\nSample: {sample}\nItem#: {item}"
    tk.Label(win, text=txt, justify="left", font=("Arial",12)).pack(pady=10)
    try:
        img = Image.open(foto_path)
        img = img.resize((300,300))
        photo = ImageTk.PhotoImage(img)
        lbl_img = tk.Label(win, image=photo)
        lbl_img.image = photo
        lbl_img.pack(pady=10)
    except:
        tk.Label(win, text="Foto tidak ditemukan", fg="red").pack(pady=10)
    def confirm():
        win.destroy()
        df = pd.read_excel(excel_file)
        if is_pinjam:
            new_data = {
                "ID": new_id,
                "Nama": nama,
                "Department": dept,
                "Sample": sample,
                "Item#": item,
                "Tanggal_Pinjam": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Tanggal_Kembali": "",
                "Foto_Pinjam": os.path.basename(foto_path),
                "Foto_Kembali": "",
                "Nama_Kembali": "",
                "Department_Kembali": "",
                "Sample_Kembali": "",
                "Item#_Kembali": "",
                "Status": "Dipinjam"
            }
            df = pd.concat([df,pd.DataFrame([new_data])], ignore_index=True)
        else:
            # pengembalian akan di-handle oleh preview_kembali
            pass
        df.to_excel(excel_file, index=False)
        refresh_list_id()
            # reset entry setelah confirm
        nama_dropdown.set("")
        entry_dept.delete(0, tk.END)
        entry_sample.delete(0, tk.END)
        entry_id_kembali.delete(0, tk.END)
        item_dropdown.set("")
        aksi_var.set(0)    # kembali ke “tidak terpilih”
        messagebox.showinfo("Success", "Data berhasil disimpan!")
    def ulang():
        win.destroy()
        if ambil_foto(foto_path):
            preview_data(new_id, nama, dept, sample, item, foto_path, is_pinjam)
    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame,text="Confirm",width=10,command=confirm).grid(row=0,column=0,padx=5)
    tk.Button(btn_frame,text="Ambil Ulang",width=10,command=ulang).grid(row=0,column=1,padx=5)

# =============================
# Fungsi Simpan Peminjaman
# =============================
def simpan_peminjaman():
    nama, dept, sample, item = nama_dropdown.get(), entry_dept.get(), entry_sample.get(), item_dropdown.get()
    if not nama or not dept or not sample:
        messagebox.showwarning("Warning","Semua field harus diisi!")
        return
    new_id = generate_new_id()
    foto_pinjam = os.path.join(foto_dir, f"{new_id}_pinjam.jpg")
    if ambil_foto(foto_pinjam):
        preview_data(new_id,nama,dept,sample,item,foto_pinjam,is_pinjam=True)

# =============================
# Fungsi Preview Pengembalian
# =============================
def preview_kembali(selected_id, foto_path):
    df = pd.read_excel(excel_file)
    row = df[df["ID"]==selected_id].iloc[0]
    win = tk.Toplevel(root)
    win.title("Preview Pengembalian")
    win.geometry("400x500")
    nama_pengembali = nama_dropdown.get()
    dept_pengembali = entry_dept.get()
    sample_pengembali = entry_sample.get()
    item_pengembali = item_dropdown.get()
    txt = f"ID: {selected_id}\nNama Pengembali: {nama_pengembali}\nDepartment: {dept_pengembali}\nSample: {sample_pengembali}\nItem#: {item_pengembali}"
    tk.Label(win,text=txt,justify="left",font=("Arial",12)).pack(pady=10)
    try:
        img = Image.open(foto_path)
        img = img.resize((300,300))
        photo = ImageTk.PhotoImage(img)
        lbl_img = tk.Label(win,image=photo)
        lbl_img.image = photo
        lbl_img.pack(pady=10)
    except:
        tk.Label(win,text="Foto tidak ditemukan",fg="red").pack(pady=10)
    def confirm():
        win.destroy()
        df.at[row.name,"Nama_Kembali"]=nama_pengembali
        df.at[row.name,"Department_Kembali"]=dept_pengembali
        df.at[row.name,"Sample_Kembali"]=sample_pengembali
        df.at[row.name,"Item#_Kembali"]=item_pengembali
        df.at[row.name,"Tanggal_Kembali"]=datetime.now().strftime("%Y-%m-%d %H:%M")
        df.at[row.name,"Foto_Kembali"]=os.path.basename(foto_path)
        df.at[row.name,"Status"]="Dikembalikan"
        df.to_excel(excel_file,index=False)
        refresh_list_id()
        # reset entry setelah confirm
        nama_dropdown.set("")
        entry_dept.delete(0, tk.END)
        item_dropdown.set("")
        aksi_var.set(0)    # kembali ke “tidak terpilih”
        entry_sample.delete(0, tk.END)
        entry_id_kembali.delete(0, tk.END)
        messagebox.showinfo("Success","Sample berhasil dikembalikan!")
    def ulang():
        win.destroy()
        if ambil_foto(foto_path):
            preview_kembali(selected_id,foto_path)
    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame,text="Confirm",width=10,command=confirm).grid(row=0,column=0,padx=5)
    tk.Button(btn_frame,text="Ambil Ulang",width=10,command=ulang).grid(row=0,column=1,padx=5)

# =============================
# Fungsi Simpan Pengembalian
# =============================
def simpan_pengembalian():
    selected = entry_id_kembali.get().strip()
    if not selected:
        messagebox.showwarning("Warning","Masukkan ID yang akan dikembalikan!")
        return
    df = pd.read_excel(excel_file)
    if selected not in df["ID"].astype(str).tolist():
        messagebox.showerror("Error","ID tidak ditemukan!")
        return
    row_index = df[df["ID"]==selected].index[0]
    if df.at[row_index,"Status"].lower()=="dikembalikan":
        messagebox.showerror("Error","ID sudah dikembalikan!")
        return
    foto_kembali = os.path.join(foto_dir,f"{selected}_kembali.jpg")
    if ambil_foto(foto_kembali):
        preview_kembali(selected,foto_kembali)

# =============================
# Fungsi Detail ID Aktif
# =============================
def show_detail(event):
    try:
        selected = listbox_id.get(listbox_id.curselection()).split(" ")[0]
    except:
        return
    df = pd.read_excel(excel_file)
    row = df[df["ID"]==selected]
    if row.empty:
        detail_text.config(text="Data tidak ditemukan")
        photo_label.config(image="",text="")
        return
    row = row.iloc[0]
    info = f"ID: {row['ID']}\nNama: {row['Nama']}\nSample: {row['Sample']}\nItem#: {row.get('Item#','')}\nDepartment: {row['Department']}\nTanggal Pinjam: {row['Tanggal_Pinjam']}"
    detail_text.config(text=info)
    foto_path = os.path.join(foto_dir,str(row.get('Foto_Pinjam','')))
    try:
        if os.path.exists(foto_path) and foto_path:
            img = Image.open(foto_path)
            img = img.resize((250,250))
            img = ImageTk.PhotoImage(img)
            photo_label.config(image=img,text="")
            photo_label.image = img
        else:
            photo_label.config(text="Foto tidak ditemukan",image="")
    except:
        photo_label.config(text="Foto tidak ditemukan",image="")

# =============================
# Fungsi History Peminjaman
# =============================
def buka_history():
    hist_win = tk.Toplevel(root)
    hist_win.title("History Peminjaman")
    hist_win.geometry("1000x550")

    df = pd.read_excel(excel_file)
    selesai = df[df["Status"]=="Dikembalikan"]

    frame_list = tk.LabelFrame(hist_win, text="ID Selesai", padx=10, pady=10)
    frame_list.pack(side="left", fill="y", padx=10, pady=10)

    # --- Input Pencarian ---
    tk.Label(frame_list, text="Cari:").pack()
    search_var = tk.StringVar()
    ent_search = tk.Entry(frame_list, textvariable=search_var, width=20)
    ent_search.pack(pady=5)

    # --- FRAME untuk LISTBOX + SCROLLBAR ---
    list_frame = tk.Frame(frame_list)
    list_frame.pack(fill="y")

    scroll_y = tk.Scrollbar(list_frame, orient="vertical")
    scroll_y.pack(side="right", fill="y")

    lb = tk.Listbox(list_frame, height=20, width=25, yscrollcommand=scroll_y.set)
    lb.pack(side="left", fill="y")

    scroll_y.config(command=lb.yview)


    # ----- Fungsi untuk menampilkan ulang list berdasarkan hasil pencarian -----
    def refresh_list():
        keyword = search_var.get().lower().strip()
        lb.delete(0, tk.END)

        for _, row in selesai.iterrows():
            text_join = (
                f"{row['ID']} "
                f"{row['Nama']} "
                f"{row.get('Nama_Kembali','')} "
                f"{row['Sample']} "
                f"{row.get('Sample_Kembali','')} "
                f"{row.get('Item#','')} "
                f"{row.get('Item#_Kembali','')}"
            ).lower()

            if keyword in text_join:
                lb.insert(tk.END, f"{row['ID']} ({row['Sample']})")

    refresh_list()

    # --- Live Search saat mengetik ---
    search_var.trace_add("write", lambda *args: refresh_list())

    # ------------------------------ FRAME DETAIL --------------------------------
    frame_detail = tk.LabelFrame(hist_win, text="Detail", padx=10, pady=10)
    frame_detail.pack(side="right", fill="both", expand=True, padx=10, pady=10)

    left_frame = tk.Frame(frame_detail)
    left_frame.pack(side="left", padx=10, pady=10, fill="y")
    right_frame = tk.Frame(frame_detail)
    right_frame.pack(side="right", padx=10, pady=10, fill="y")

    lbl_hist_left = tk.Label(left_frame, text="Pilih ID untuk melihat detail")
    lbl_hist_left.pack()
    lbl_hist_right = tk.Label(right_frame, text="")
    lbl_hist_right.pack()

    lbl_foto_left = tk.Label(left_frame)
    lbl_foto_left.pack(pady=5)
    lbl_foto_right = tk.Label(right_frame)
    lbl_foto_right.pack(pady=5)

    def show_hist_detail(event):
        try:
            sid = lb.get(lb.curselection()).split(" ")[0]
        except:
            return
        
        row = selesai[selesai["ID"] == sid].iloc[0]

        info_left = (
            f"--- Meminjam ---\n"
            f"Nama: {row['Nama']}\n"
            f"Department: {row['Department']}\n"
            f"Sample: {row['Sample']}\n"
            f"Item#: {row.get('Item#','')}\n"
            f"Tanggal Pinjam: {row['Tanggal_Pinjam']}"
        )

        info_right = (
            f"--- Mengembalikan ---\n"
            f"Nama: {row.get('Nama_Kembali','')}\n"
            f"Department: {row.get('Department_Kembali','')}\n"
            f"Sample: {row.get('Sample_Kembali','')}\n"
            f"Item#: {row.get('Item#_Kembali','')}\n"
            f"Tanggal Kembali: {row['Tanggal_Kembali']}"
        )

        lbl_hist_left.config(text=info_left)
        lbl_hist_right.config(text=info_right)

        # foto kiri
        try:
            img1 = Image.open(os.path.join(foto_dir, row['Foto_Pinjam']))
            img1 = img1.resize((300, 300))
            photo1 = ImageTk.PhotoImage(img1)
            lbl_foto_left.config(image=photo1, text="")
            lbl_foto_left.image = photo1
        except:
            lbl_foto_left.config(text="Foto pinjam tidak ditemukan", image="")

        # foto kanan
        try:
            img2 = Image.open(os.path.join(foto_dir, row['Foto_Kembali']))
            img2 = img2.resize((300, 300))
            photo2 = ImageTk.PhotoImage(img2)
            lbl_foto_right.config(image=photo2, text="")
            lbl_foto_right.image = photo2
        except:
            lbl_foto_right.config(text="Foto kembali tidak ditemukan", image="")

    lb.bind("<<ListboxSelect>>", show_hist_detail)

def open_about_window():
    about = tk.Toplevel(root)
    about.title("About")
    about.geometry("420x350")
    about.resizable(False, False)
    about.grab_set()  # Lock popup

    # ===== FRAME untuk logo agar bisa horizontal =====
    logo_frame = tk.Frame(about)
    logo_frame.pack(pady=20)

    # ==== LOAD LOGO PT LBJ ====
    try:
        logo_pt = Image.open(os.path.join(base_dir, "logo_lbj.png"))
        logo_pt = logo_pt.resize((120, 120), Image.LANCZOS)
        photo_pt = ImageTk.PhotoImage(logo_pt)
        lbl_pt = tk.Label(logo_frame, image=photo_pt)
        lbl_pt.image = photo_pt
        lbl_pt.pack(side="left", padx=15)
    except:
        tk.Label(logo_frame, text="Logo PT tidak ditemukan").pack(side="left", padx=15)

    # ==== LOAD LOGO FQC ====
    try:
        logo_fqc = Image.open(os.path.join(base_dir, "logo_fqc.png"))
        logo_fqc = logo_fqc.resize((120, 120), Image.LANCZOS)
        photo_fqc = ImageTk.PhotoImage(logo_fqc)
        lbl_fqc = tk.Label(logo_frame, image=photo_fqc)
        lbl_fqc.image = photo_fqc
        lbl_fqc.pack(side="left", padx=15)
    except:
        tk.Label(logo_frame, text="Logo FQC tidak ditemukan").pack(side="left", padx=15)

    # ===== TEXT ABOUT =====
    text = (
        "PT Langgeng Buana Jaya\n"
        "Final Quality Control\n"
        "Tracking Sample\n"
        "V3.1\n\n"
        "Dibuat oleh Team FQC Penghancur Pintu Part 2."
    )

    tk.Label(
        about,
        text=text,
        font=("Arial", 12),
        justify="center"
    ).pack(pady=10)

def backup_data():
    try:
        # Format nama folder backup: DDMMYYYY HH.MM
        timestamp = datetime.now().strftime("%d%m%Y %H.%M")
        backup_dir = os.path.join(base_dir, timestamp)

        # Buat folder backup
        os.makedirs(backup_dir, exist_ok=False)

        # ---- Backup file Excel ----
        excel_backup_path = os.path.join(backup_dir, "record_peminjaman.xlsx")
        shutil.copy2(excel_file, excel_backup_path)

        # ---- Backup folder foto ----
        foto_backup_path = os.path.join(backup_dir, "foto")
        if os.path.exists(foto_dir):
            shutil.copytree(foto_dir, foto_backup_path)

        messagebox.showinfo(
            "Backup Sukses",
            f"Backup berhasil dibuat di:\n{backup_dir}"
        )

    except Exception as e:
        messagebox.showerror(
            "Backup Gagal",
            f"Terjadi kesalahan saat backup:\n{str(e)}"
        )




# =============================
# GUI Setup
# =============================
root = tk.Tk()
# Set App Icon menggunakan logo FQC
try:
    icon_path = os.path.join(base_dir, "logo_fqc.ico")
    icon_img = ImageTk.PhotoImage(Image.open(icon_path))
    root.iconphoto(True, icon_img)
except:
    print("Icon aplikasi gagal dimuat")

root.title("PT. Langgeng Buana Jaya - Tracking Sample QC")
root.geometry("1000x600")

header = tk.Label(root,text="PT. Langgeng Buana Jaya\nFinal Quality Control\nTracking Sample",font=("Arial",16,"bold"))
header.grid(row=0,column=0,columnspan=3,pady=10)

aksi_frame = tk.LabelFrame(root,text="Aksi",padx=10,pady=10)
aksi_frame.grid(row=1,column=0,padx=10,pady=10,sticky="w")
aksi_var = tk.IntVar(value=0)
tk.Radiobutton(aksi_frame,text="Meminjam",variable=aksi_var,value=1).pack(anchor="w")
tk.Radiobutton(aksi_frame,text="Mengembalikan",variable=aksi_var,value=2).pack(anchor="w")

form_frame = tk.LabelFrame(root,text="Input Data",padx=10,pady=10)
form_frame.grid(row=2,column=0,padx=10,pady=10,sticky="n")
tk.Label(form_frame,text="Nama").grid(row=0,column=0,sticky="w")



def on_name_selected(value):
    row = df_name[df_name["Name"] == value]
    if not row.empty:
        entry_dept.delete(0, tk.END)
        entry_dept.insert(0, row.iloc[0]["Department"])

nama_dropdown = SearchableDropdown(
    form_frame,
    values=name_values,
    width=20,
    on_select=on_name_selected
)
nama_dropdown.grid(row=0, column=1, sticky="w")

tk.Label(form_frame,text="Department").grid(row=1,column=0,sticky="w")

def on_dept_selected(value):
    # otomatis isi nama jika unik pada department
    row = df_name[df_name["Department"] == value]
    if len(row) == 1:
        nama_dropdown.set(row.iloc[0]["Name"])

entry_dept = tk.Entry(form_frame, width=22)
entry_dept.grid(row=1, column=1, sticky="w")

tk.Label(form_frame,text="Item#").grid(row=2,column=0,sticky="w")
item_values = ["Other"] + df_item["DropdownText"].astype(str).tolist()

def on_item_selected(value):
    if value == "Other":
        entry_sample.delete(0, tk.END)
        return

    item_number = value.split(" ")[0]
    row = df_item[df_item["Item#"].astype(str) == item_number]

    if not row.empty:
        entry_sample.delete(0, tk.END)
        entry_sample.insert(0, row.iloc[0]["Sample"])

# Ganti combobox dengan widget custom
item_dropdown = SearchableDropdown(form_frame, item_values, on_select=on_item_selected, width=20)
item_dropdown.grid(row=2, column=1, sticky="w")

tk.Label(form_frame,text="Sample").grid(row=3,column=0,sticky="w")
entry_sample = tk.Entry(form_frame, width=22)
entry_sample.grid(row=3,column=1)


tk.Label(form_frame,text="ID Kembali").grid(row=4,column=0,sticky="w")
entry_id_kembali = tk.Entry(form_frame, width=22)
entry_id_kembali.grid(row=4,column=1)

btn_submit = tk.Button(form_frame,text="Proses")
def proses_aksi():
    if aksi_var.get() == 1:
        simpan_peminjaman()
    elif aksi_var.get() == 2:
        simpan_pengembalian()
    else:
        messagebox.showwarning("Warning", "Pilih aksi terlebih dahulu!")

btn_submit = tk.Button(form_frame, text="Proses", width=20, command=proses_aksi)

btn_submit.grid(row=5,column=0,columnspan=2,pady=10)
btn_about = tk.Button(form_frame, text="About", command=open_about_window, width=20)
btn_about.grid(row=8, column=0, columnspan=2, pady=5)
btn_history = tk.Button(form_frame,text="History Peminjaman",width=20,command=buka_history)
btn_history.grid(row=6,column=0,columnspan=2,pady=10)
btn_backup = tk.Button(form_frame, text="Back Up", width=20, command=backup_data)
btn_backup.grid(row=7, column=0, columnspan=2, pady=5)

list_frame = tk.LabelFrame(root,text="ID Aktif (Belum Kembali)",padx=10,pady=10)
list_frame.grid(row=2,column=1,padx=10,pady=10,sticky="n")
listbox_id = tk.Listbox(list_frame,height=15,width=25)
listbox_id.pack()
listbox_id.bind("<<ListboxSelect>>", show_detail)

detail_frame = tk.LabelFrame(root,text="Detail Peminjaman",padx=10,pady=10)
detail_frame.grid(row=2,column=2,padx=10,pady=10,sticky="n")
detail_text = tk.Label(detail_frame,text="Klik ID untuk melihat detail")
detail_text.pack()
photo_label = tk.Label(detail_frame)
photo_label.pack(pady=5)

refresh_list_id()
root.mainloop()
