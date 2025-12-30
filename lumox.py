import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
import phonenumbers
from phonenumbers import carrier, timezone
import requests
import threading
import socket
import whois
import webbrowser
import os

sites = {
    "Github": "https://github.com/{}",
    "Reddit": "https://www.reddit.com/user/{}",
    "Youtube": "https://www.youtube.com/@{}",
    "Tiktok": "https://www.tiktok.com/@{}",
    "Pastebin": "https://pastebin.com/u/{}",
    "Steam": "https://steamcommunity.com/id/{}"
}

class SplashScreen:
    def __init__(self, root, logo_path="logo.png", duration=3000):
        self.root = root
        self.duration = duration
        self.photo = None
        
        self.root.geometry("250x200")
        self.root.configure(bg="#0a0a0a")
        self.root.overrideredirect(True)
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        x = (screen_width - 250) // 2
        y = (screen_height - 200) // 2
        
        self.root.geometry(f"250x200+{x}+{y}")
        self.root.update_idletasks()
        
        try:
            self.root.attributes("-topmost", True)
        except:
            pass
        
        main_frame = tk.Frame(self.root, bg="#0a0a0a")
        main_frame.pack(expand=True, fill=tk.BOTH)
        
        logo_found = False
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path)
                img = img.resize((100, 100), Image.Resampling.LANCZOS)
                self.photo = ImageTk.PhotoImage(img)
                logo_label = tk.Label(main_frame, image=self.photo, bg="#0a0a0a")
                logo_label.pack(expand=True)
                logo_found = True
            except:
                pass
        
        if not logo_found:
            label = tk.Label(main_frame, text="Lumox", font=("Segoe UI", 24, "bold"), 
                           fg="#808080", bg="#0a0a0a")
            label.pack(expand=True)
        
        self.root.update()
        self.root.after(self.duration, self.close_splash)
    
    def close_splash(self):
        self.root.destroy()

class PlaceholderEntry(tk.Entry):
    def __init__(self, parent, placeholder, **kwargs):
        super().__init__(parent, **kwargs)
        self.placeholder = placeholder
        self.active = False
        self.bind("<FocusIn>", self.clear)
        self.bind("<FocusOut>", self.restore)
        self.restore()

    def clear(self, e=None):
        if self.active:
            self.delete(0, tk.END)
            self.config(fg="#808080")
            self.active = False

    def restore(self, e=None):
        if not self.get():
            self.insert(0, self.placeholder)
            self.config(fg="#505050")
            self.active = True

    def get_text(self):
        return "" if self.active else self.get()

class BaseLookup:
    def __init__(self, parent, label, placeholder, action):
        self.frame = tk.Frame(parent, bg="#0a0a0a")
        self.action = action
        self.running = False

        top = tk.Frame(self.frame, bg="#0a0a0a")
        top.pack(fill=tk.X, padx=30, pady=(30, 20))

        tk.Label(top, text=label, font=("Segoe UI", 11),
                 fg="#808080", bg="#0a0a0a").pack(anchor="w", pady=(0, 10))

        row = tk.Frame(top, bg="#0a0a0a")
        row.pack(fill=tk.X)

        self.entry = PlaceholderEntry(
            row, placeholder, font=("Segoe UI", 10),
            bg="#1a1a1a", fg="#808080",
            insertbackground="#808080", bd=0
        )
        self.entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 12), ipady=10)

        self.button = tk.Button(row, text="Lookup", command=self.safe_action,
                  bg="#2a2a2a", fg="#808080",
                  bd=0, padx=25, pady=10)
        self.button.pack(side=tk.RIGHT)

        self.output = tk.Text(self.frame, font=("Segoe UI", 10),
                              bg="#1a1a1a", fg="#808080",
                              state=tk.DISABLED, bd=0,
                              padx=12, pady=12)
        self.output.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 30))

    def safe_action(self):
        if not self.running:
            self.action()

    def write(self, text):
        self.output.config(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, text)
        self.output.config(state=tk.DISABLED)

class PhoneLookup(BaseLookup):
    def __init__(self, parent):
        super().__init__(parent, "Phone Number", "+1 (123) 456-7890", self.lookup)

    def lookup(self):
        phone = self.entry.get_text()
        if not phone:
            return
        self.running = True
        self.button.config(state=tk.DISABLED)
        threading.Thread(target=self.process, args=(phone,), daemon=True).start()

    def process(self, phone):
        try:
            p = phonenumbers.parse(phone)
            out = f"Number: {phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.INTERNATIONAL)}\n"
            out += f"Country: {phonenumbers.region_code_for_number(p)}\n"
            out += f"Carrier: {carrier.name_for_number(p, 'en') or 'Unknown'}\n"
            out += f"Timezone: {', '.join(timezone.time_zones_for_number(p))}\n"
            out += f"Valid: {'Yes' if phonenumbers.is_valid_number(p) else 'No'}"
        except Exception as e:
            out = f"Error: {e}"
        self.write(out)
        self.running = False
        self.button.config(state=tk.NORMAL)

class IPLookup(BaseLookup):
    def __init__(self, parent):
        super().__init__(parent, "IP Address", "123.45.67.89", self.lookup)

    def lookup(self):
        ip = self.entry.get_text()
        if not ip:
            return
        self.running = True
        self.button.config(state=tk.DISABLED)
        threading.Thread(target=self.process, args=(ip,), daemon=True).start()

    def process(self, ip):
        try:
            r = requests.get(f"http://ip-api.com/json/{ip}", timeout=10).json()
            out = "\n".join([f"{k}: {v}" for k, v in r.items()])
        except Exception as e:
            out = f"Error: {e}"
        self.write(out)
        self.running = False
        self.button.config(state=tk.NORMAL)

class UsernameLookup(BaseLookup):
    def __init__(self, parent):
        super().__init__(parent, "Username", "username", self.lookup)

    def lookup(self):
        u = self.entry.get_text()
        if not u:
            return
        self.running = True
        self.button.config(state=tk.DISABLED)
        threading.Thread(target=self.process, args=(u,), daemon=True).start()

    def process(self, u):
        out = ""
        for name, url in sites.items():
            try:
                r = requests.get(url.format(u), timeout=10)
                out += f"{name}: {'FOUND' if r.status_code == 200 else 'NOT FOUND'}\n"
            except:
                out += f"{name}: ERROR\n"
        self.write(out)
        self.running = False
        self.button.config(state=tk.NORMAL)

class DomainLookup(BaseLookup):
    def __init__(self, parent):
        super().__init__(parent, "Domain", "example.com", self.lookup)

    def lookup(self):
        d = self.entry.get_text()
        if not d:
            return
        self.running = True
        self.button.config(state=tk.DISABLED)
        threading.Thread(target=self.process, args=(d,), daemon=True).start()

    def process(self, d):
        try:
            out = f"IP: {socket.gethostbyname(d)}\n"
            w = whois.whois(d)
            out += f"Registrar: {w.registrar}\n"
        except:
            out = "Lookup failed"
        self.write(out)
        self.running = False
        self.button.config(state=tk.NORMAL)

class GoogleDork:
    def __init__(self, parent):
        self.frame = tk.Frame(parent, bg="#0a0a0a")

        top = tk.Frame(self.frame, bg="#0a0a0a")
        top.pack(fill=tk.X, padx=30, pady=(30, 20))

        tk.Label(top, text="Target", font=("Segoe UI", 11),
                 fg="#808080", bg="#0a0a0a").pack(anchor="w", pady=(0, 10))

        self.entry = PlaceholderEntry(
            top, "",
            font=("Segoe UI", 10),
            bg="#1a1a1a", fg="#808080",
            insertbackground="#808080", bd=0
        )
        self.entry.pack(fill=tk.X, ipady=10)

        btns = tk.Frame(self.frame, bg="#0a0a0a")
        btns.pack(pady=20)

        for text, cmd in [
            ("SITE", self.site),
            ("INURL", self.inurl),
            ("INTITLE", self.intitle),
            ("FILETYPE", self.filetype),
            ("CACHE", self.cache)
        ]:
            tk.Button(btns, text=text, command=cmd,
                      bg="#1a1a1a", fg="#808080",
                      bd=0, padx=20, pady=10).pack(side=tk.LEFT, padx=8)

    def open(self, query):
        webbrowser.open(f"https://www.google.com/search?q={query}")

    def site(self):
        t = self.entry.get_text()
        if t:
            self.open(f"site:{t}")

    def inurl(self):
        t = self.entry.get_text()
        if t:
            self.open(f"inurl:{t}")

    def intitle(self):
        t = self.entry.get_text()
        if t:
            self.open(f"intitle:{t}")

    def cache(self):
        t = self.entry.get_text()
        if t:
            self.open(f"cache:{t}")

    def filetype(self):
        t = self.entry.get_text()
        if not t:
            return
        ft = simpledialog.askstring("Filetype", "Enter file type")
        if ft:
            self.open(f"filetype:{ft} {t}")

class Credits:
    def __init__(self, parent):
        self.frame = tk.Frame(parent, bg="#0a0a0a")
        tk.Label(self.frame, text="Credits", font=("Segoe UI", 16, "bold"),
                 fg="#808080", bg="#0a0a0a").pack(pady=40)
        text = tk.Text(self.frame, bg="#1a1a1a", fg="#808080",
                       bd=0, padx=12, pady=12)
        text.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        text.insert(tk.END, "Website:\nhttps://salvatorerusso.xyz/\n\nGithub:\nhttps://github.com/skun0\n\nDeveloped by Skuno")
        text.config(state=tk.DISABLED)

class MainApp:
    def __init__(self, root):
        root.title("Lumox")
        root.geometry("900x650")
        root.configure(bg="#0a0a0a")

        nav = tk.Frame(root, bg="#0a0a0a", height=60)
        nav.pack(fill=tk.X)

        bar = tk.Frame(nav, bg="#0a0a0a")
        bar.pack(side=tk.LEFT, padx=30, pady=15)

        self.content = tk.Frame(root, bg="#0a0a0a")
        self.content.pack(fill=tk.BOTH, expand=True)

        self.modules = {
            "Phone": PhoneLookup(self.content),
            "IP": IPLookup(self.content),
            "Username": UsernameLookup(self.content),
            "Domain": DomainLookup(self.content),
            "Google Dork": GoogleDork(self.content),
            "Credits": Credits(self.content)
        }

        for name, mod in self.modules.items():
            tk.Button(bar, text=name, bg="#1a1a1a",
                      fg="#808080", bd=0,
                      padx=20, pady=8,
                      command=lambda m=mod: self.show(m.frame)).pack(side=tk.LEFT, padx=8)

        self.show(self.modules["Phone"].frame)

    def show(self, frame):
        for w in self.content.winfo_children():
            w.pack_forget()
        frame.pack(fill=tk.BOTH, expand=True)

def main():
    splash = tk.Tk()
    SplashScreen(splash)
    splash.mainloop()

    root = tk.Tk()
    MainApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
