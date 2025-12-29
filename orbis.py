import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw
import phonenumbers
from phonenumbers import carrier, timezone
import requests
import threading
import webbrowser

class SplashScreen:
    def __init__(self, root, logo_path, duration=3000):
        self.root = root
        self.duration = duration
        
        self.root.geometry("250x200")
        self.root.configure(bg="#0a0a0a")
        self.root.overrideredirect(True)
        
        try:
            self.root.wm_attributes("-topmost", True)
        except:
            pass
        
        self.center_window()
        
        main_frame = tk.Frame(self.root, bg="#0a0a0a")
        main_frame.pack(expand=True, fill=tk.BOTH)
        
        try:
            img = Image.open(logo_path)
            img = img.resize((100, 100), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(img)
            logo_label = tk.Label(main_frame, image=self.photo, bg="#0a0a0a")
            logo_label.pack(expand=True)
        except:
            label = tk.Label(main_frame, text="ORBIS", font=("Segoe UI", 24, "bold"), 
                           fg="#808080", bg="#0a0a0a")
            label.pack(expand=True)
        
        self.root.after(self.duration, self.close_splash)
    
    def center_window(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")
    
    def close_splash(self):
        self.root.destroy()
    
    def create_rounded_image(self, img, radius):
        size = img.size
        mask = Image.new('L', size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
        rounded = Image.new('RGBA', size)
        rounded.paste(img, (0, 0))
        rounded.putalpha(mask)
        return rounded

class PlaceholderEntry(tk.Entry):
    def __init__(self, parent, placeholder, **kwargs):
        super().__init__(parent, **kwargs)
        self.placeholder = placeholder
        self.placeholder_active = False
        self.bind("<FocusIn>", self.on_focus_in)
        self.bind("<FocusOut>", self.on_focus_out)
        self.show_placeholder()
    
    def show_placeholder(self):
        self.placeholder_active = True
        self.insert(0, self.placeholder)
        self.config(fg="#505050")
    
    def on_focus_in(self, event):
        if self.placeholder_active:
            self.delete(0, tk.END)
            self.config(fg="#808080")
            self.placeholder_active = False
    
    def on_focus_out(self, event):
        if not self.get():
            self.show_placeholder()
    
    def get_text(self):
        if self.placeholder_active:
            return ""
        return self.get()

class PhoneLookup:
    def __init__(self, parent):
        self.frame = tk.Frame(parent, bg="#0a0a0a")
        
        input_frame = tk.Frame(self.frame, bg="#0a0a0a")
        input_frame.pack(fill=tk.X, padx=30, pady=(30, 20))
        
        label = tk.Label(input_frame, text="Phone Number", font=("Segoe UI", 11), 
                        fg="#808080", bg="#0a0a0a")
        label.pack(anchor="w", pady=(0, 10))
        
        entry_button_frame = tk.Frame(input_frame, bg="#0a0a0a")
        entry_button_frame.pack(fill=tk.X)
        
        self.entry = PlaceholderEntry(entry_button_frame, "+1 (123) 456-7890", 
                                     font=("Segoe UI", 10), 
                                     bg="#1a1a1a", fg="#808080", 
                                     insertbackground="#808080", bd=0, relief=tk.FLAT)
        self.entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 12), ipady=10)
        
        self.lookup_btn = tk.Button(entry_button_frame, text="Lookup", 
                                    font=("Segoe UI", 10, "bold"), 
                                    bg="#2a2a2a", fg="#808080", bd=0, 
                                    relief=tk.FLAT, padx=25, pady=10,
                                    command=self.lookup)
        self.lookup_btn.pack(side=tk.RIGHT)
        self.lookup_btn.bind("<Enter>", lambda e: self.lookup_btn.config(bg="#353535"))
        self.lookup_btn.bind("<Leave>", lambda e: self.lookup_btn.config(bg="#2a2a2a"))
        
        output_frame = tk.Frame(self.frame, bg="#0a0a0a")
        output_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 30))
        
        output_label = tk.Label(output_frame, text="Result", font=("Segoe UI", 11), 
                               fg="#808080", bg="#0a0a0a")
        output_label.pack(anchor="w", pady=(0, 10))
        
        scrollbar = tk.Scrollbar(output_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.output = tk.Text(output_frame, font=("Segoe UI", 10), 
                             bg="#1a1a1a", fg="#808080", 
                             state=tk.DISABLED, bd=0, relief=tk.FLAT,
                             yscrollcommand=scrollbar.set, padx=12, pady=12)
        self.output.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.output.yview)
    
    def lookup(self):
        phone = self.entry.get_text().strip()
        if not phone:
            messagebox.showwarning("Input Error", "Please enter a phone number")
            return
        
        self.lookup_btn.config(state=tk.DISABLED)
        self.output.config(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, "Looking up...")
        self.output.config(state=tk.DISABLED)
        
        thread = threading.Thread(target=self.perform_lookup, args=(phone,))
        thread.daemon = True
        thread.start()
    
    def perform_lookup(self, phone):
        try:
            parsed = phonenumbers.parse(phone, None)
            
            country = phonenumbers.region_code_for_number(parsed)
            carrier_name = carrier.name_for_number(parsed, "en")
            timezone_list = timezone.time_zones_for_number(parsed)
            is_valid = phonenumbers.is_valid_number(parsed)
            is_possible = phonenumbers.is_possible_number(parsed)
            formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
            number_type = phonenumbers.number_type(parsed)
            
            type_map = {
                0: "FIXED_LINE",
                1: "MOBILE",
                2: "FIXED_LINE_OR_MOBILE",
                3: "TOLL_FREE",
                4: "PREMIUM_RATE",
                5: "SHARED_COST",
                6: "VOIP",
                7: "PERSONAL_NUMBER",
                8: "PAGER",
                9: "UAN",
                10: "VOICEMAIL",
                11: "UNKNOWN"
            }
            
            type_name = type_map.get(number_type, "UNKNOWN")
            
            result = f"Number: {formatted}\n"
            result += f"Country Code: {parsed.country_code}\n"
            result += f"National Number: {parsed.national_number}\n"
            result += f"Country: {country}\n"
            result += f"Carrier: {carrier_name if carrier_name else 'Unknown'}\n"
            result += f"Type: {type_name}\n"
            result += f"Timezone: {', '.join(timezone_list) if timezone_list else 'Unknown'}\n"
            result += f"Valid: {'Yes' if is_valid else 'No'}\n"
            result += f"Possible: {'Yes' if is_possible else 'No'}"
            
            self.output.config(state=tk.NORMAL)
            self.output.delete("1.0", tk.END)
            self.output.insert(tk.END, result)
            self.output.config(state=tk.DISABLED)
        except Exception as e:
            self.output.config(state=tk.NORMAL)
            self.output.delete("1.0", tk.END)
            self.output.insert(tk.END, f"Error: {str(e)}")
            self.output.config(state=tk.DISABLED)
        finally:
            self.lookup_btn.config(state=tk.NORMAL)

class IPLookup:
    def __init__(self, parent):
        self.frame = tk.Frame(parent, bg="#0a0a0a")
        
        input_frame = tk.Frame(self.frame, bg="#0a0a0a")
        input_frame.pack(fill=tk.X, padx=30, pady=(30, 20))
        
        label = tk.Label(input_frame, text="IP Address", font=("Segoe UI", 11), 
                        fg="#808080", bg="#0a0a0a")
        label.pack(anchor="w", pady=(0, 10))
        
        entry_button_frame = tk.Frame(input_frame, bg="#0a0a0a")
        entry_button_frame.pack(fill=tk.X)
        
        self.entry = PlaceholderEntry(entry_button_frame, "123.45.67.89", 
                                     font=("Segoe UI", 10), 
                                     bg="#1a1a1a", fg="#808080", 
                                     insertbackground="#808080", bd=0, relief=tk.FLAT)
        self.entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 12), ipady=10)
        
        self.lookup_btn = tk.Button(entry_button_frame, text="Lookup", 
                                    font=("Segoe UI", 10, "bold"), 
                                    bg="#2a2a2a", fg="#808080", bd=0, 
                                    relief=tk.FLAT, padx=25, pady=10,
                                    command=self.lookup, cursor="hand2")
        self.lookup_btn.pack(side=tk.RIGHT)
        self.lookup_btn.bind("<Enter>", lambda e: self.lookup_btn.config(bg="#353535"))
        self.lookup_btn.bind("<Leave>", lambda e: self.lookup_btn.config(bg="#2a2a2a"))
        
        output_frame = tk.Frame(self.frame, bg="#0a0a0a")
        output_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 30))
        
        output_label = tk.Label(output_frame, text="Result", font=("Segoe UI", 11), 
                               fg="#808080", bg="#0a0a0a")
        output_label.pack(anchor="w", pady=(0, 10))
        
        scrollbar = tk.Scrollbar(output_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.output = tk.Text(output_frame, font=("Segoe UI", 10), 
                             bg="#1a1a1a", fg="#808080", 
                             state=tk.DISABLED, bd=0, relief=tk.FLAT,
                             yscrollcommand=scrollbar.set, padx=12, pady=12)
        self.output.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.output.yview)
    
    def lookup(self):
        ip = self.entry.get_text().strip()
        if not ip:
            messagebox.showwarning("Input Error", "Please enter an IP address")
            return
        
        self.lookup_btn.config(state=tk.DISABLED)
        self.output.config(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, "Looking up...")
        self.output.config(state=tk.DISABLED)
        
        thread = threading.Thread(target=self.perform_lookup, args=(ip,))
        thread.daemon = True
        thread.start()
    
    def perform_lookup(self, ip):
        try:
            response = requests.get(f"http://ip-api.com/json/{ip}", timeout=10)
            data = response.json()
            
            if data.get("status") == "fail":
                self.output.config(state=tk.NORMAL)
                self.output.delete("1.0", tk.END)
                self.output.insert(tk.END, f"Error: {data.get('message', 'IP not found')}")
                self.output.config(state=tk.DISABLED)
                return
            
            result = f"IP: {data.get('query', 'N/A')}\n"
            result += f"Country: {data.get('country', 'N/A')}\n"
            result += f"Country Code: {data.get('countryCode', 'N/A')}\n"
            result += f"Region: {data.get('region', 'N/A')}\n"
            result += f"Region Name: {data.get('regionName', 'N/A')}\n"
            result += f"City: {data.get('city', 'N/A')}\n"
            result += f"Zip: {data.get('zip', 'N/A')}\n"
            result += f"Latitude: {data.get('lat', 'N/A')}\n"
            result += f"Longitude: {data.get('lon', 'N/A')}\n"
            result += f"Timezone: {data.get('timezone', 'N/A')}\n"
            result += f"ISP: {data.get('isp', 'N/A')}\n"
            result += f"Organization: {data.get('org', 'N/A')}\n"
            result += f"AS: {data.get('as', 'N/A')}"
            
            self.output.config(state=tk.NORMAL)
            self.output.delete("1.0", tk.END)
            self.output.insert(tk.END, result)
            self.output.config(state=tk.DISABLED)
        except Exception as e:
            self.output.config(state=tk.NORMAL)
            self.output.delete("1.0", tk.END)
            self.output.insert(tk.END, f"Error: {str(e)}")
            self.output.config(state=tk.DISABLED)
        finally:
            self.lookup_btn.config(state=tk.NORMAL)

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Orbis")
        self.root.geometry("900x650")
        self.root.configure(bg="#0a0a0a")
        self.root.minsize(700, 500)
        
        try:
            self.root.iconbitmap("logo.png")
        except:
            pass
        
        navbar = tk.Frame(self.root, bg="#0a0a0a", height=60)
        navbar.pack(side=tk.TOP, fill=tk.X)
        navbar.pack_propagate(False)
        
        nav_buttons = tk.Frame(navbar, bg="#0a0a0a")
        nav_buttons.pack(side=tk.LEFT, padx=30, pady=15)
        
        self.phone_btn = tk.Button(nav_buttons, text="Phone Lookup", font=("Segoe UI", 10, "bold"),
                                   bg="#2a2a2a", fg="#808080", bd=0, relief=tk.FLAT,
                                   padx=20, pady=8, command=self.show_phone, cursor="hand2")
        self.phone_btn.pack(side=tk.LEFT, padx=8)
        self.phone_btn.bind("<Enter>", lambda e: self.phone_btn.config(bg="#353535"))
        self.phone_btn.bind("<Leave>", lambda e: self.phone_btn.config(bg="#2a2a2a"))
        
        self.ip_btn = tk.Button(nav_buttons, text="IP Lookup", font=("Segoe UI", 10, "bold"),
                               bg="#1a1a1a", fg="#808080", bd=0, relief=tk.FLAT,
                               padx=20, pady=8, command=self.show_ip, cursor="hand2")
        self.ip_btn.pack(side=tk.LEFT, padx=8)
        self.ip_btn.bind("<Enter>", lambda e: self.ip_btn.config(bg="#252525"))
        self.ip_btn.bind("<Leave>", lambda e: self.ip_btn.config(bg="#1a1a1a"))
        
        self.credits_btn = tk.Button(nav_buttons, text="Credits", font=("Segoe UI", 10, "bold"),
                               bg="#1a1a1a", fg="#808080", bd=0, relief=tk.FLAT,
                               padx=20, pady=8, command=self.show_credits, cursor="hand2")
        self.credits_btn.pack(side=tk.LEFT, padx=8)
        self.credits_btn.bind("<Enter>", lambda e: self.credits_btn.config(bg="#252525"))
        self.credits_btn.bind("<Leave>", lambda e: self.credits_btn.config(bg="#1a1a1a"))
        
        self.content = tk.Frame(self.root, bg="#0a0a0a")
        self.content.pack(fill=tk.BOTH, expand=True)
        
        self.phone_lookup = PhoneLookup(self.content)
        self.ip_lookup = IPLookup(self.content)
        self.credits = self.create_credits()
        
        self.show_phone()
    
    def create_credits(self):
        frame = tk.Frame(self.content, bg="#0a0a0a")
        
        title = tk.Label(frame, text="Credits", font=("Segoe UI", 16, "bold"), 
                        fg="#808080", bg="#0a0a0a")
        title.pack(pady=(40, 30))
        
        links_frame = tk.Frame(frame, bg="#0a0a0a")
        links_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        label = tk.Label(links_frame, text="Links", font=("Segoe UI", 11), 
                        fg="#808080", bg="#0a0a0a")
        label.pack(anchor="w", pady=(0, 10))
        
        scrollbar = tk.Scrollbar(links_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.credits_output = tk.Text(links_frame, font=("Segoe UI", 10), 
                             bg="#1a1a1a", fg="#808080", 
                             state=tk.DISABLED, bd=0, relief=tk.FLAT,
                             yscrollcommand=scrollbar.set, padx=12, pady=12)
        self.credits_output.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.credits_output.yview)
        
        self.credits_output.config(state=tk.NORMAL)
        self.credits_output.insert(tk.END, "Website:\nhttps://salvatorerusso.xyz/\n\nGithub:\nhttps://github.com/skun0")
        self.credits_output.config(state=tk.DISABLED)
        
        return frame
    
    def show_phone(self):
        self.ip_lookup.frame.pack_forget()
        self.credits.pack_forget()
        self.phone_lookup.frame.pack(fill=tk.BOTH, expand=True)
        self.phone_btn.config(bg="#2a2a2a", fg="#808080")
        self.ip_btn.config(bg="#1a1a1a", fg="#808080")
        self.credits_btn.config(bg="#1a1a1a", fg="#808080")
    
    def show_ip(self):
        self.phone_lookup.frame.pack_forget()
        self.credits.pack_forget()
        self.ip_lookup.frame.pack(fill=tk.BOTH, expand=True)
        self.phone_btn.config(bg="#1a1a1a", fg="#808080")
        self.ip_btn.config(bg="#2a2a2a", fg="#808080")
        self.credits_btn.config(bg="#1a1a1a", fg="#808080")
    
    def show_credits(self):
        self.phone_lookup.frame.pack_forget()
        self.ip_lookup.frame.pack_forget()
        self.credits.pack(fill=tk.BOTH, expand=True)
        self.phone_btn.config(bg="#1a1a1a", fg="#808080")
        self.ip_btn.config(bg="#1a1a1a", fg="#808080")
        self.credits_btn.config(bg="#2a2a2a", fg="#808080")

def main():
    splash_root = tk.Tk()
    SplashScreen(splash_root, "logo.png", duration=3000)
    splash_root.mainloop()
    
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()