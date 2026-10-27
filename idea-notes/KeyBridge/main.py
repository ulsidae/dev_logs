import ctypes
import ctypes.wintypes as wt
import tkinter as tk
from tkinter import messagebox
import threading, queue, json, os, sys

if os.name != "nt":
    raise SystemExit("KeyBridge requires Windows OS.")

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
WM_QUIT = 0x0012
LLKHF_INJECTED = 0x10
LLKHF_UP = 0x80
KEYEVENTF_KEYUP = 0x0002

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(sys.argv[0])),
    "keybridge.json"
)

STARTUP_DIR = os.path.join(
    os.environ.get("APPDATA", ""),
    r"Microsoft\Windows\Start Menu\Programs\Startup"
)
STARTUP_FILE = os.path.join(STARTUP_DIR, "KeyBridge.vbs")

class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wt.DWORD),
        ("scanCode", wt.DWORD),
        ("flags", wt.DWORD),
        ("time", wt.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


HOOKPROC = ctypes.WINFUNCTYPE(
    wt.LPARAM,
    ctypes.c_int,
    wt.WPARAM,
    wt.LPARAM
)

user32.SetWindowsHookExW.argtypes = [
    ctypes.c_int, HOOKPROC, wt.HINSTANCE, wt.DWORD
]
user32.SetWindowsHookExW.restype = wt.HHOOK

user32.CallNextHookEx.argtypes = [
    wt.HHOOK, ctypes.c_int, wt.WPARAM, wt.LPARAM
]
user32.CallNextHookEx.restype = wt.LPARAM

user32.UnhookWindowsHookEx.argtypes = [wt.HHOOK]
user32.UnhookWindowsHookEx.restype = wt.BOOL

user32.GetMessageW.argtypes = [
    ctypes.POINTER(wt.MSG), wt.HWND, wt.UINT, wt.UINT
]
user32.GetMessageW.restype = ctypes.c_int

user32.PostThreadMessageW.argtypes = [
    wt.DWORD, wt.UINT, wt.WPARAM, wt.LPARAM
]
user32.PostThreadMessageW.restype = wt.BOOL

user32.keybd_event.argtypes = [
    wt.BYTE, wt.BYTE, wt.DWORD, ctypes.c_size_t
]
user32.keybd_event.restype = None

kernel32.GetModuleHandleW.argtypes = [wt.LPCWSTR]
kernel32.GetModuleHandleW.restype = wt.HMODULE

kernel32.GetCurrentThreadId.restype = wt.DWORD

KEY_ROWS = [
    [
        ("Esc", 0x1B, 1),
        ("F1", 0x70, 1), ("F2", 0x71, 1),
        ("F3", 0x72, 1), ("F4", 0x73, 1),
        ("F5", 0x74, 1), ("F6", 0x75, 1),
        ("F7", 0x76, 1), ("F8", 0x77, 1),
        ("F9", 0x78, 1), ("F10", 0x79, 1),
        ("F11", 0x7A, 1), ("F12", 0x7B, 1),
    ],
    [
        ("`", 0xC0, 1), ("1", 0x31, 1),
        ("2", 0x32, 1), ("3", 0x33, 1),
        ("4", 0x34, 1), ("5", 0x35, 1),
        ("6", 0x36, 1), ("7", 0x37, 1),
        ("8", 0x38, 1), ("9", 0x39, 1),
        ("0", 0x30, 1), ("-", 0xBD, 1),
        ("=", 0xBB, 1), ("Back", 0x08, 2),
    ],
    [
        ("Tab", 0x09, 1.5), ("Q", 0x51, 1),
        ("W", 0x57, 1), ("E", 0x45, 1),
        ("R", 0x52, 1), ("T", 0x54, 1),
        ("Y", 0x59, 1), ("U", 0x55, 1),
        ("I", 0x49, 1), ("O", 0x4F, 1),
        ("P", 0x50, 1), ("[", 0xDB, 1),
        ("]", 0xDD, 1), ("\\", 0xDC, 1.5),
    ],
    [
        ("Caps", 0x14, 1.8), ("A", 0x41, 1),
        ("S", 0x53, 1), ("D", 0x44, 1),
        ("F", 0x46, 1), ("G", 0x47, 1),
        ("H", 0x48, 1), ("J", 0x4A, 1),
        ("K", 0x4B, 1), ("L", 0x4C, 1),
        (";", 0xBA, 1), ("'", 0xDE, 1),
        ("Enter", 0x0D, 2.2),
    ],
    [
        ("LShift", 0xA0, 2.3), ("Z", 0x5A, 1),
        ("X", 0x58, 1), ("C", 0x43, 1),
        ("V", 0x56, 1), ("B", 0x42, 1),
        ("N", 0x4E, 1), ("M", 0x4D, 1),
        (",", 0xBC, 1), (".", 0xBE, 1),
        ("/", 0xBF, 1), ("RShift", 0xA1, 2.7),
    ],
    [
        ("LCtrl", 0xA2, 1.3), ("LWin", 0x5B, 1.2),
        ("LAlt", 0xA4, 1.2), ("Space", 0x20, 5.5),
        ("RAlt", 0xA5, 1.2), ("RWin", 0x5C, 1.2),
        ("Menu", 0x5D, 1.2), ("RCtrl", 0xA3, 1.3),
    ],
    [
        ("Ins", 0x2D, 1), ("Home", 0x24, 1),
        ("PgUp", 0x21, 1), ("Del", 0x2E, 1),
        ("End", 0x23, 1), ("PgDn", 0x22, 1),
        ("↑", 0x26, 1), ("←", 0x25, 1),
        ("↓", 0x28, 1), ("→", 0x27, 1),
    ],
]

VK_NAMES = {
    0x08: "Backspace", 0x09: "Tab",
    0x0D: "Enter", 0x14: "Caps Lock",
    0x1B: "Escape", 0x20: "Space",
    0x21: "Page Up", 0x22: "Page Down",
    0x23: "End", 0x24: "Home",
    0x25: "Left", 0x26: "Up",
    0x27: "Right", 0x28: "Down",
    0x2D: "Insert", 0x2E: "Delete",
    0x5B: "Left Win", 0x5C: "Right Win",
    0x5D: "Menu", 0xA0: "Left Shift",
    0xA1: "Right Shift", 0xA2: "Left Ctrl",
    0xA3: "Right Ctrl", 0xA4: "Left Alt",
    0xA5: "Right Alt",
}

for row in KEY_ROWS:
    for label, vk, width in row:
        VK_NAMES.setdefault(vk, label)

class KeyBridge:
    def __init__(self, root):
        self.root = root
        self.root.title("v 1.0")
        self.root.configure(bg="#171923")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.lock = threading.RLock()
        self.events = queue.Queue()

        self.mapping = {}
        self.enabled = True
        self.capture_mode = None
        self.captured_keys = set()
        self.selected_source = None
        self.selected_target = None

        self.key_buttons = {}
        self.hook_handle = None
        self.hook_thread_id = None
        self.hook_ready = threading.Event()
        self.hook_error = None
        self.closing = False

        self.load_config()
        self.build_ui()

        self.hook_thread = threading.Thread(
            target=self.hook_worker,
            name="KeyBridgeHook",
            daemon=True
        )
        self.hook_thread.start()

        self.root.after(30, self.process_events)
        self.root.after(100, self.check_hook_status)

        self.refresh_keys()
        self.refresh_mapping_list()

    def load_config(self):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.mapping = {
                int(k): int(v)
                for k, v in data.get("mapping", {}).items()
            }
            self.enabled = bool(data.get("enabled", True))
        except (OSError, ValueError, TypeError):
            self.mapping = {}
            self.enabled = True

    def save_config(self):
        try:
            with self.lock:
                data = {
                    "mapping": self.mapping.copy(),
                    "enabled": self.enabled,
                }

            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

        except OSError as exc:
            messagebox.showerror("Save Error", str(exc))

    def build_ui(self):
        outer = tk.Frame(
            self.root, bg="#171923", padx=16, pady=14
        )
        outer.pack()

        tk.Label(
            outer, text="KEYBRIDGE",
            bg="#171923", fg="#f7fafc",
            font=("Segoe UI", 19, "bold")
        ).pack(anchor="w")

        tk.Label(
            outer, text="By ulsidae",
            bg="#171923", fg="#a0aec0",
            font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(0, 12))

        board = tk.Frame(
            outer, bg="#252a3a", padx=8, pady=8
        )
        board.pack()

        for row in KEY_ROWS:
            line = tk.Frame(board, bg="#252a3a")
            line.pack(anchor="w", pady=2)

            for label, vk, width in row:
                btn = tk.Button(
                    line,
                    text=label,
                    width=max(4, int(width * 5)),
                    height=2,
                    relief="flat",
                    bd=0,
                    bg="#353b4d",
                    fg="#edf2f7",
                    activebackground="#667eea",
                    activeforeground="white",
                    font=("Segoe UI", 8, "bold"),
                    command=lambda code=vk: self.key_clicked(code),
                )
                btn.pack(side="left", padx=2)
                self.key_buttons.setdefault(vk, []).append(btn)

        panel = tk.Frame(outer, bg="#171923")
        panel.pack(fill="x", pady=(12, 0))

        self.instruction = tk.Label(
            panel,
            text="Click a source key, then click a target key.",
            bg="#171923", fg="#cbd5e0",
            font=("Segoe UI", 9)
        )
        self.instruction.pack(anchor="w", pady=(0, 8))

        actions = tk.Frame(panel, bg="#171923")
        actions.pack(fill="x")

        self.source_label = tk.Label(
            actions, text="Source: —", width=17, anchor="w",
            bg="#252a3a", fg="#f7fafc", padx=6, pady=8
        )
        self.source_label.pack(side="left", padx=(0, 5))

        self.target_label = tk.Label(
            actions, text="Target: —", width=17, anchor="w",
            bg="#252a3a", fg="#f7fafc", padx=6, pady=8
        )
        self.target_label.pack(side="left", padx=(0, 5))

        tk.Button(
            actions, text="Capture Source",
            command=lambda: self.start_capture("source"),
            bg="#805ad5", fg="white",
            relief="flat", padx=7, pady=7
        ).pack(side="left", padx=3)

        tk.Button(
            actions, text="Capture Target",
            command=lambda: self.start_capture("target"),
            bg="#2b6cb0", fg="white",
            relief="flat", padx=7, pady=7
        ).pack(side="left", padx=3)

        options = tk.Frame(panel, bg="#171923")
        options.pack(fill="x", pady=(9, 0))

        tk.Button(
            options, text="Apply Mapping",
            command=self.apply_mapping,
            bg="#667eea", fg="white",
            relief="flat", padx=12, pady=8
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            options, text="Remove Selected",
            command=self.remove_mapping,
            bg="#4a5568", fg="white",
            relief="flat", padx=10, pady=8
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            options, text="Reset Selection",
            command=self.reset_selection,
            bg="#4a5568", fg="white",
            relief="flat", padx=10, pady=8
        ).pack(side="left", padx=(0, 8))

        self.enabled_var = tk.BooleanVar(value=self.enabled)

        tk.Checkbutton(
            options, text="Enable",
            variable=self.enabled_var,
            command=self.toggle_enabled,
            bg="#171923", fg="#f7fafc",
            selectcolor="#252a3a",
            activebackground="#171923",
            activeforeground="#f7fafc",
            font=("Segoe UI", 9)
        ).pack(side="left")

        tk.Label(
            panel, text="Active mappings",
            bg="#171923", fg="#f7fafc",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(12, 4))

        self.mapping_list = tk.Listbox(
            panel, height=5, width=85,
            bg="#252a3a", fg="#e2e8f0",
            selectbackground="#667eea",
            relief="flat", font=("Consolas", 10),
            activestyle="none"
        )
        self.mapping_list.pack(fill="x")
        self.mapping_list.bind(
            "<<ListboxSelect>>", self.list_selected
        )

        footer = tk.Frame(panel, bg="#171923")
        footer.pack(fill="x", pady=(8, 0))

        tk.Button(
            footer, text="Save Settings",
            command=self.save_config,
            bg="#2f855a", fg="white",
            relief="flat", padx=10, pady=7
        ).pack(side="left")

        tk.Button(
            footer, text="Toggle Auto-Start",
            command=self.toggle_startup,
            bg="#4a5568", fg="white",
            relief="flat", padx=10, pady=7
        ).pack(side="left", padx=7)

        tk.Label(
            footer, text="Windows | Standard library only",
            bg="#171923", fg="#718096",
            font=("Segoe UI", 8)
        ).pack(side="right")

    def key_name(self, vk):
        if vk is None:
            return "—"
        return VK_NAMES.get(vk, f"VK {vk:02X}")

    def key_clicked(self, vk):
        with self.lock:
            mode = self.capture_mode

        if mode:
            self.events.put(("capture", mode, vk))
            return

        if self.selected_source is None:
            self.selected_source = vk
            self.selected_target = None
            self.instruction.config(
                text="Select a target key."
            )
        elif self.selected_target is None:
            self.selected_target = vk
            self.instruction.config(
                text="Click Apply Mapping to activate."
            )
        else:
            self.selected_source = vk
            self.selected_target = None
            self.instruction.config(
                text="Select a target key."
            )

        self.update_selection_labels()
        self.refresh_keys()

    def start_capture(self, mode):
        with self.lock:
            self.capture_mode = mode
            self.captured_keys.clear()

        self.instruction.config(
            text=f"Press a physical key to capture {mode.upper()}..."
        )

    def finish_capture(self, mode, vk):
        if mode == "source":
            self.selected_source = vk
            self.selected_target = None
            self.instruction.config(
                text="Source captured. Capture the target key."
            )
        else:
            self.selected_target = vk
            self.instruction.config(
                text="Target captured. Click Apply Mapping."
            )

        self.update_selection_labels()
        self.refresh_keys()

    def update_selection_labels(self):
        self.source_label.config(
            text=f"Source: {self.key_name(self.selected_source)}"
        )
        self.target_label.config(
            text=f"Target: {self.key_name(self.selected_target)}"
        )

    def reset_selection(self):
        self.selected_source = None
        self.selected_target = None

        with self.lock:
            self.capture_mode = None
            self.captured_keys.clear()

        self.instruction.config(
            text="Click a source key, then click a target key."
        )
        self.update_selection_labels()
        self.refresh_keys()

    def apply_mapping(self):
        src = self.selected_source
        dst = self.selected_target

        if src is None or dst is None:
            messagebox.showinfo(
                "Selection Required",
                "Select both a source key and a target key."
            )
            return

        if src == dst:
            messagebox.showinfo(
                "Invalid Mapping",
                "Source and target must be different."
            )
            return

        with self.lock:
            self.mapping[src] = dst

        self.save_config()
        self.refresh_mapping_list()
        self.reset_selection()

    def remove_mapping(self):
        selected = self.mapping_list.curselection()

        if selected:
            sources = sorted(
                self.mapping,
                key=lambda vk: self.key_name(vk).lower()
            )
            index = selected[0]

            if index < len(sources):
                with self.lock:
                    self.mapping.pop(sources[index], None)
        elif self.selected_source is not None:
            with self.lock:
                self.mapping.pop(self.selected_source, None)
        else:
            messagebox.showinfo(
                "Select a Mapping",
                "Select a mapping from the list first."
            )
            return

        self.save_config()
        self.refresh_mapping_list()
        self.refresh_keys()

    def list_selected(self, _event=None):
        selected = self.mapping_list.curselection()
        if not selected:
            return

        with self.lock:
            sources = sorted(
                self.mapping,
                key=lambda vk: self.key_name(vk).lower()
            )
            index = selected[0]

            if index >= len(sources):
                return

            src = sources[index]
            dst = self.mapping[src]

        self.selected_source = src
        self.selected_target = dst
        self.update_selection_labels()
        self.refresh_keys()

    def refresh_mapping_list(self):
        self.mapping_list.delete(0, tk.END)

        with self.lock:
            items = sorted(
                self.mapping.items(),
                key=lambda item: self.key_name(item[0]).lower()
            )
            enabled = self.enabled

        for src, dst in items:
            status = "ACTIVE" if enabled else "DISABLED"
            self.mapping_list.insert(
                tk.END,
                f"{self.key_name(src)} -> "
                f"{self.key_name(dst)} [{status}]"
            )

        self.refresh_keys()

    def refresh_keys(self):
        with self.lock:
            mapping = self.mapping.copy()
            enabled = self.enabled

        for vk, buttons in self.key_buttons.items():
            if vk == self.selected_source:
                bg, fg = "#d69e2e", "#171923"
            elif vk == self.selected_target:
                bg, fg = "#38a169", "white"
            elif vk in mapping:
                bg = "#667eea" if enabled else "#4a5568"
                fg = "white"
            else:
                bg, fg = "#353b4d", "#edf2f7"

            for button in buttons:
                button.configure(bg=bg, fg=fg)

    def toggle_enabled(self):
        with self.lock:
            self.enabled = self.enabled_var.get()

        self.save_config()
        self.refresh_mapping_list()

    def hook_worker(self):
        self.hook_thread_id = kernel32.GetCurrentThreadId()

        msg = wt.MSG()
        user32.PeekMessageW(
            ctypes.byref(msg), None, 0, 0, 0
        )

        callback = HOOKPROC(self.keyboard_hook)

        hook = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL,
            callback,
            kernel32.GetModuleHandleW(None),
            0
        )

        if not hook:
            self.hook_error = ctypes.get_last_error()
            self.hook_ready.set()
            return

        self.hook_handle = hook

        self.hook_callback = callback
        self.hook_ready.set()

        try:
            while True:
                result = user32.GetMessageW(
                    ctypes.byref(msg), None, 0, 0
                )

                if result <= 0:
                    break

                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            if self.hook_handle:
                user32.UnhookWindowsHookEx(self.hook_handle)
                self.hook_handle = None

    def keyboard_hook(self, n_code, w_param, l_param):
        try:
            if n_code < 0:
                return user32.CallNextHookEx(
                    self.hook_handle, n_code, w_param, l_param
                )

            info = ctypes.cast(
                l_param,
                ctypes.POINTER(KBDLLHOOKSTRUCT)
            ).contents

            vk = int(info.vkCode)
            flags = int(info.flags)

            if flags & LLKHF_INJECTED:
                return user32.CallNextHookEx(
                    self.hook_handle, n_code, w_param, l_param
                )

            is_up = bool(flags & LLKHF_UP) or (
                w_param in (WM_KEYUP, WM_SYSKEYUP)
            )
            is_down = w_param in (WM_KEYDOWN, WM_SYSKEYDOWN)

            with self.lock:
                capture_mode = self.capture_mode

                if capture_mode and is_down:
                    self.capture_mode = None
                    self.captured_keys.add(vk)
                    self.events.put(("capture", capture_mode, vk))
                    return 1

                if is_up and vk in self.captured_keys:
                    self.captured_keys.discard(vk)
                    return 1

                if not self.enabled:
                    return user32.CallNextHookEx(
                        self.hook_handle, n_code, w_param, l_param
                    )

                target = self.mapping.get(vk)

            if target is not None:
                if is_down:
                    user32.keybd_event(
                        target, 0, 0, 0x4B425247
                    )
                    return 1

                if is_up:
                    user32.keybd_event(
                        target, 0, KEYEVENTF_KEYUP, 0x4B425247
                    )
                    return 1

        except Exception:
            pass

        return user32.CallNextHookEx(
            self.hook_handle, n_code, w_param, l_param
        )

    def check_hook_status(self):
        if not self.hook_ready.is_set():
            if not self.closing:
                self.root.after(100, self.check_hook_status)
            return

        if self.hook_error:
            messagebox.showerror(
                "Keyboard Hook Error",
                f"Unable to install keyboard hook.\n"
                f"Windows error code: {self.hook_error}"
            )

    def process_events(self):
        if self.closing:
            return

        try:
            while True:
                event = self.events.get_nowait()

                if event[0] == "capture":
                    _, mode, vk = event
                    self.finish_capture(mode, vk)

        except queue.Empty:
            pass

        self.root.after(20, self.process_events)

    def toggle_startup(self):
        try:
            os.makedirs(STARTUP_DIR, exist_ok=True)

            if os.path.exists(STARTUP_FILE):
                os.remove(STARTUP_FILE)
                messagebox.showinfo(
                    "Auto-Start",
                    "KeyBridge has been removed from startup."
                )
                return

            python_exe = sys.executable

            if os.path.basename(python_exe).lower() == "python.exe":
                candidate = os.path.join(
                    os.path.dirname(python_exe), "pythonw.exe"
                )
                if os.path.exists(candidate):
                    python_exe = candidate

            script = os.path.abspath(sys.argv[0])

            def vbs_quote(value):
                return '"' + value.replace('"', '""') + '"'

            command = (
                vbs_quote(python_exe) + " " + vbs_quote(script)
            )

            with open(STARTUP_FILE, "w", encoding="utf-8") as f:
                f.write(
                    'Set WshShell = CreateObject("WScript.Shell")\n'
                )
                f.write(
                    "WshShell.Run " + vbs_quote(command) + ", 0, False\n"
                )

            messagebox.showinfo(
                "Auto-Start",
                "KeyBridge will start when you sign in to Windows."
            )

        except OSError as exc:
            messagebox.showerror("Auto-Start Error", str(exc))

    def on_close(self):
        self.closing = True

        with self.lock:
            self.capture_mode = None

        if self.hook_thread_id:
            user32.PostThreadMessageW(
                self.hook_thread_id, WM_QUIT, 0, 0
            )

        self.root.destroy()


def main():
    root = tk.Tk()
    KeyBridge(root)
    root.mainloop()


if __name__ == "__main__":
    main()
