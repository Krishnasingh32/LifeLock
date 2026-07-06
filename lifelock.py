# LifeLock - CREATIVE EDITION
# Fullscreen lockdown with 3D effects, animations and fancy visuals

import json
import time
import threading
import random
import psutil
import winsound
from datetime import datetime
from plyer import notification
import tkinter as tk
from tkinter import messagebox, simpledialog
import math

FILENAME = "activities.json"

BLOCKED_APPS = [
    "chrome.exe", "firefox.exe", "msedge.exe",
    "spotify.exe", "discord.exe", "steam.exe",
    "EpicGamesLauncher.exe", "valorant.exe",
    "Telegram.exe", "WhatsApp.exe",
]

GUILT_MESSAGES = [
    "😤 YOU SKIPPED THIS. AGAIN. GET UP.",
    "💀 Every second you waste, someone else is getting ahead.",
    "🔥 Your future self is BEGGING you to do this right now.",
    "😠 Stop being lazy. You PROMISED yourself. DO IT.",
    "⏰ Time is running out. Your habits decide your destiny.",
    "🚫 NO EXCUSES. NO SHORTCUTS. DO THE WORK.",
    "👁️ LifeLock sees everything. You cannot hide.",
    "💔 You're letting yourself down right now. FIX IT.",
    "🎯 Champions don't skip. What are you choosing to be?",
    "😡 GET OFF YOUR PHONE AND DO WHAT YOU SAID YOU WOULD.",
]

# ── Global state ─────────────────────────────────────────
activities = []
blocking_active = False
lockdown_window = None
lockdown_active = False

# ── Core functions ───────────────────────────────────────

def load_activities():
    try:
        with open(FILENAME, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_activities():
    with open(FILENAME, "w") as f:
        json.dump(activities, f, indent=4)

def get_time():
    return datetime.now().strftime("%H:%M")

def get_date():
    return datetime.now().strftime("%A, %d %B %Y")

def get_minutes_overdue(act_time):
    now = datetime.now()
    due = datetime.strptime(act_time, "%H:%M").replace(
        year=now.year, month=now.month, day=now.day
    )
    return max(0, int((now - due).total_seconds() // 60))

def play_alarm(intensity=1):
    def _play():
        for _ in range(intensity * 3):
            winsound.Beep(1000 + (intensity * 200), 200)
            time.sleep(0.05)
    threading.Thread(target=_play, daemon=True).start()

def kill_blocked_apps():
    killed = []
    for proc in psutil.process_iter(["name"]):
        try:
            if proc.info["name"] in BLOCKED_APPS:
                proc.kill()
                killed.append(proc.info["name"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return killed

def get_overdue():
    now = get_time()
    return [a for a in activities if a["time"] <= now and not a.get("done_today")]

# ── PARTICLE CANVAS ANIMATION ────────────────────────────

class ParticleCanvas:
    """Animated floating particles in the background"""
    def __init__(self, parent, width, height):
        self.canvas = tk.Canvas(
            parent, width=width, height=height,
            bg="#000000", highlightthickness=0
        )
        self.canvas.place(x=0, y=0)
        self.width = width
        self.height = height
        self.particles = []
        self.running = True
        for _ in range(60):
            self.particles.append({
                "x": random.randint(0, width),
                "y": random.randint(0, height),
                "r": random.uniform(1, 3),
                "dx": random.uniform(-0.5, 0.5),
                "dy": random.uniform(-0.8, -0.2),
                "color": random.choice([
                    "#FF0000", "#FF3300", "#FF6600",
                    "#FF0044", "#CC0000", "#FF4444"
                ]),
                "id": None
            })
        self.animate()

    def animate(self):
        if not self.running:
            return
        self.canvas.delete("particle")
        for p in self.particles:
            p["x"] += p["dx"]
            p["y"] += p["dy"]
            if p["y"] < 0:
                p["y"] = self.height
                p["x"] = random.randint(0, self.width)
            if p["x"] < 0 or p["x"] > self.width:
                p["x"] = random.randint(0, self.width)
            r = p["r"]
            self.canvas.create_oval(
                p["x"]-r, p["y"]-r, p["x"]+r, p["y"]+r,
                fill=p["color"], outline="", tags="particle"
            )
        self.canvas.after(30, self.animate)

    def stop(self):
        self.running = False


class GlowLabel:
    """Label with animated glow/pulse effect"""
    def __init__(self, parent, text, font_size, color="#FF0000",
                 glow_color="#FF4400", x=0, y=0):
        self.parent = parent
        self.text = text
        self.color = color
        self.glow_color = glow_color
        self.angle = 0
        self.running = True

        # Shadow layers for 3D effect
        for dx, dy in [(3,3),(2,2),(1,1)]:
            tk.Label(
                parent, text=text,
                font=("Impact", font_size, "bold"),
                bg="#000000",
                fg="#330000"
            ).place(x=x+dx, y=y+dy, anchor="center")

        # Main label
        self.label = tk.Label(
            parent, text=text,
            font=("Impact", font_size, "bold"),
            bg="#000000", fg=color
        )
        self.label.place(x=x, y=y, anchor="center")
        self.pulse()

    def pulse(self):
        if not self.running:
            return
        self.angle += 0.1
        # Oscillate between red and orange for glow effect
        r = int(255)
        g = int(abs(math.sin(self.angle)) * 80)
        b = 0
        color = f"#{r:02x}{g:02x}{b:02x}"
        self.label.config(fg=color)
        self.label.after(50, self.pulse)

    def stop(self):
        self.running = False


class ThreeDBlock:
    """A block with 3D raised effect using canvas"""
    def __init__(self, parent, text, x, y, width=600,
                 fg="#FF4444", overdue_mins=0):
        frame = tk.Frame(parent, bg="#000000")
        frame.place(x=x, y=y, anchor="center", width=width)

        canvas = tk.Canvas(
            frame, width=width, height=70,
            bg="#000000", highlightthickness=0
        )
        canvas.pack()

        # 3D shadow layers (dark bottom/right)
        canvas.create_rectangle(
            6, 6, width-2, 66,
            fill="#1a0000", outline=""
        )
        # 3D highlight (bright top/left edge)
        canvas.create_rectangle(
            2, 2, width-6, 62,
            fill="#2d0000", outline=""
        )
        # Main face
        canvas.create_rectangle(
            4, 2, width-8, 60,
            fill="#1a0000", outline="#FF2200", width=1
        )
        # Left bright edge
        canvas.create_line(4, 2, 4, 60, fill="#FF4400", width=2)
        # Top bright edge
        canvas.create_line(4, 2, width-8, 2, fill="#FF4400", width=2)
        # Right dark edge
        canvas.create_line(width-8, 2, width-8, 60, fill="#550000", width=2)
        # Bottom dark edge
        canvas.create_line(4, 60, width-8, 60, fill="#550000", width=2)

        # ❌ icon
        canvas.create_text(
            30, 31, text="✗",
            font=("Arial", 20, "bold"),
            fill="#FF0000"
        )

        # Activity name
        canvas.create_text(
            width//2, 20,
            text=text,
            font=("Arial", 14, "bold"),
            fill="#FF6666"
        )

        # Overdue time
        canvas.create_text(
            width//2, 42,
            text=f"⏰  Overdue by  {overdue_mins}  minutes",
            font=("Arial", 11),
            fill="#FF3300"
        )

        self.canvas = canvas
        self._mins = overdue_mins
        self._text = text

    def update_mins(self, mins):
        self.canvas.delete("timer")
        self.canvas.create_text(
            300, 42,
            text=f"⏰  Overdue by  {mins}  minutes",
            font=("Arial", 11),
            fill="#FF3300",
            tags="timer"
        )


class TypewriterLabel:
    """Text that types itself character by character"""
    def __init__(self, parent, text, font_size=13,
                 color="#FFAAAA", delay=40, x=0, y=0):
        self.label = tk.Label(
            parent, text="",
            font=("Courier", font_size),
            bg="#000000", fg=color
        )
        self.label.place(x=x, y=y, anchor="center")
        self.full_text = text
        self.current = 0
        self.delay = delay
        self.type_next()

    def type_next(self):
        if self.current <= len(self.full_text):
            self.label.config(text=self.full_text[:self.current] + "█")
            self.current += 1
            self.label.after(self.delay, self.type_next)
        else:
            self.label.config(text=self.full_text)


# ── LOCKDOWN WINDOW ──────────────────────────────────────

def create_lockdown_window(overdue_acts):
    global lockdown_window, lockdown_active
    if lockdown_active:
        return

    lockdown_active = True
    lockdown_window = tk.Toplevel(root)
    lockdown_window.title("LIFELOCK")
    lockdown_window.attributes("-fullscreen", True)
    lockdown_window.attributes("-topmost", True)
    lockdown_window.configure(bg="#000000")
    lockdown_window.protocol("WM_DELETE_WINDOW", lambda: None)
    lockdown_window.bind("<Alt-F4>", lambda e: None)
    lockdown_window.bind("<Escape>", lambda e: None)
    lockdown_window.grab_set()
    lockdown_window.focus_force()

    SW = lockdown_window.winfo_screenwidth()
    SH = lockdown_window.winfo_screenheight()

    # ── Particle background ──
    particles = ParticleCanvas(lockdown_window, SW, SH)

    # ── Glowing title ──
    GlowLabel(
        lockdown_window,
        text="⛓  L I F E L O C K  ⛓",
        font_size=52,
        x=SW//2, y=100
    )

    # ── Subtitle with typewriter ──
    TypewriterLabel(
        lockdown_window,
        text="▸▸  Y O U   H A V E   U N F I N I S H E D   B U S I N E S S  ◂◂",
        font_size=14,
        color="#FF6666",
        delay=35,
        x=SW//2, y=180
    )

    # ── Animated guilt message ──
    guilt_var = tk.StringVar(value=random.choice(GUILT_MESSAGES))
    guilt_label = tk.Label(
        lockdown_window,
        textvariable=guilt_var,
        font=("Georgia", 15, "italic"),
        bg="#000000", fg="#FF9966",
        wraplength=900
    )
    guilt_label.place(x=SW//2, y=240, anchor="center")

    # ── Divider line ──
    tk.Canvas(
        lockdown_window,
        width=700, height=2,
        bg="#000000", highlightthickness=0
    ).create_line(0, 1, 700, 1, fill="#FF2200", width=2)
    tk.Label(
        lockdown_window,
        text="◆  COMPLETE THESE TO UNLOCK YOUR SCREEN  ◆",
        font=("Arial", 13, "bold"),
        bg="#000000", fg="#FF4400"
    ).place(x=SW//2, y=290, anchor="center")

    # ── 3D activity blocks ──
    block_objects = []
    start_y = 340
    for act in overdue_acts:
        mins = get_minutes_overdue(act["time"])
        block = ThreeDBlock(
            lockdown_window,
            text=act["name"],
            x=SW//2,
            y=start_y,
            width=min(700, SW-100),
            overdue_mins=mins
        )
        block_objects.append((act, block))
        start_y += 90

    # ── Pulsing countdown ──
    countdown_var = tk.StringVar()
    countdown_label = tk.Label(
        lockdown_window,
        textvariable=countdown_var,
        font=("Courier", 12, "bold"),
        bg="#000000", fg="#FF3300"
    )
    countdown_label.place(x=SW//2, y=start_y + 10, anchor="center")

    def update_blocks():
        if lockdown_active and lockdown_window.winfo_exists():
            for act, block in block_objects:
                if not act.get("done_today"):
                    block.update_mins(get_minutes_overdue(act["time"]))
            guilt_var.set(random.choice(GUILT_MESSAGES))
            countdown_var.set(
                f"⏱  Apps blocked · Screen locked · {get_time()}  ⏱"
            )
            lockdown_window.after(30000, update_blocks)

    update_blocks()

    # ── Mark done button ──
    btn_frame = tk.Frame(lockdown_window, bg="#000000")
    btn_frame.place(x=SW//2, y=start_y + 55, anchor="center")

    def lockdown_mark_done():
        global lockdown_active
        name = simpledialog.askstring(
            "✅ Mark Complete",
            "Type the EXACT name of the activity you completed:",
            parent=lockdown_window
        )
        if not name:
            return

        matched = False
        for act in activities:
            if act["name"].lower() == name.lower().strip():
                act["done_today"] = True
                act["last_done"] = get_time()
                matched = True
                save_activities()
                break

        if not matched:
            messagebox.showerror(
                "❌ Not Found",
                f"'{name}' not found.\nType it exactly as shown on screen!",
                parent=lockdown_window
            )
            return

        still_overdue = get_overdue()
        if not still_overdue:
            particles.stop()
            lockdown_active = False
            lockdown_window.grab_release()
            lockdown_window.destroy()
            refresh_list()
            play_alarm(1)
            messagebox.showinfo(
                "🔓 FREEDOM UNLOCKED!",
                "✅ ALL DONE!\n\nYou earned your freedom!\nApps are unblocked. Well done! 🎉"
            )
        else:
            # Update display
            for act, block in block_objects:
                if act.get("done_today"):
                    block.canvas.delete("all")
                    block.canvas.create_rectangle(
                        4, 2, 692, 60,
                        fill="#001a00", outline="#00FF44", width=1
                    )
                    block.canvas.create_text(
                        350, 31,
                        text=f"✅  {act['name']}  —  COMPLETED!",
                        font=("Arial", 14, "bold"),
                        fill="#44FF88"
                    )
            messagebox.showinfo(
                "✅ Good!",
                f"'{name}' done!\n\nStill {len(still_overdue)} more to complete.",
                parent=lockdown_window
            )

    # Animated button
    done_btn = tk.Button(
        btn_frame,
        text="  ✅   I  C O M P L E T E D  A N  A C T I V I T Y  ",
        font=("Arial", 13, "bold"),
        bg="#003300", fg="#00FF66",
        activebackground="#006600",
        activeforeground="#ffffff",
        borderwidth=0,
        padx=25, pady=14,
        cursor="hand2",
        relief="flat",
        command=lockdown_mark_done
    )
    done_btn.pack()

    # Button hover effects
    def on_enter(e):
        done_btn.config(bg="#006600")
    def on_leave(e):
        done_btn.config(bg="#003300")

    done_btn.bind("<Enter>", on_enter)
    done_btn.bind("<Leave>", on_leave)

    # ── Button pulse animation ──
    btn_glow = True
    def pulse_btn():
        nonlocal btn_glow
        if lockdown_active and lockdown_window.winfo_exists():
            btn_glow = not btn_glow
            done_btn.config(
                fg="#00FF66" if btn_glow else "#AAFFAA"
            )
            lockdown_window.after(600, pulse_btn)
    pulse_btn()

    play_alarm(3)


def trigger_lockdown():
    global blocking_active
    overdue = get_overdue()
    if overdue and not lockdown_active:
        blocking_active = True
        kill_blocked_apps()
        root.after(0, lambda: create_lockdown_window(overdue))


# ── Background monitor ───────────────────────────────────

def background_monitor():
    while True:
        time.sleep(30)
        overdue = get_overdue()
        if overdue:
            kill_blocked_apps()
            if not lockdown_active:
                root.after(0, trigger_lockdown)
        try:
            root.after(0, refresh_list)
        except:
            pass


# ── MAIN GUI ─────────────────────────────────────────────

def refresh_list():
    listbox.delete(0, tk.END)
    for act in activities:
        status = "✅" if act.get("done_today") else "⬜"
        now = get_time()
        overdue = act["time"] <= now and not act.get("done_today")
        mins = f"  (+{get_minutes_overdue(act['time'])} min)" if overdue else ""
        listbox.insert(
            tk.END,
            f"  {status}  {act['time']}   {act['name']}{mins}"
        )
        if overdue:
            listbox.itemconfig(tk.END, fg="#FF4444")
        elif act.get("done_today"):
            listbox.itemconfig(tk.END, fg="#44FF88")

    overdue = get_overdue()
    if overdue:
        status_label.config(
            text=f"⛓  {len(overdue)} OVERDUE — LOCKDOWN INCOMING!",
            fg="#FF4444"
        )
    else:
        status_label.config(
            text="✅  All on track!  Apps unlocked.  🔓",
            fg="#44FF88"
        )

def update_clock():
    clock_label.config(text=f"⊛  {get_time()}   ·   {get_date()}")
    root.after(1000, update_clock)

def btn_add():
    name = simpledialog.askstring(
        "Add Activity", "Activity name:", parent=root
    )
    if not name:
        return
    time_str = simpledialog.askstring(
        "Add Activity", "Time (HH:MM e.g. 07:00):", parent=root
    )
    if not time_str:
        return
    try:
        datetime.strptime(time_str, "%H:%M")
    except ValueError:
        messagebox.showerror("Error", "Invalid time! Use HH:MM")
        return
    activities.append({
        "name": name.strip(),
        "time": time_str.strip(),
        "done_today": False,
        "last_done": None
    })
    activities.sort(key=lambda x: x["time"])
    save_activities()
    refresh_list()

def btn_mark_done():
    selected = listbox.curselection()
    if not selected:
        messagebox.showwarning("Select", "Click an activity first!")
        return
    idx = selected[0]
    activities[idx]["done_today"] = True
    activities[idx]["last_done"] = get_time()
    save_activities()
    refresh_list()
    if not get_overdue():
        messagebox.showinfo("🔓 Free!", "All done! You earned it! 🎉")

def btn_delete():
    selected = listbox.curselection()
    if not selected:
        messagebox.showwarning("Select", "Click an activity first!")
        return
    idx = selected[0]
    name = activities[idx]["name"]
    if messagebox.askyesno("Delete", f"Delete '{name}'?"):
        activities.pop(idx)
        save_activities()
        refresh_list()

def btn_trigger_now():
    overdue = get_overdue()
    if overdue:
        trigger_lockdown()
    else:
        messagebox.showinfo("✅ Clear!", "No overdue activities!")

def on_close():
    global lockdown_active
    if lockdown_active:
        messagebox.showwarning(
            "🔒 Locked!",
            "Complete your overdue activities first!"
        )
    else:
        save_activities()
        root.destroy()

# ── BUILD MAIN WINDOW ────────────────────────────────────

root = tk.Tk()
root.title("LifeLock 🔒")
root.geometry("620x580")
root.configure(bg="#0a0a0a")
root.resizable(False, False)
root.protocol("WM_DELETE_WINDOW", on_close)

# Gradient-style header using canvas
header = tk.Canvas(
    root, width=620, height=90,
    bg="#0a0a0a", highlightthickness=0
)
header.pack()

# Draw gradient header
for i in range(90):
    r = min(255, i * 3)
    color = f"#{r:02x}00{max(0, 30-i):02x}"
    header.create_line(0, i, 620, i, fill=color)

header.create_text(
    310, 35,
    text="⛓  L I F E L O C K  ⛓",
    font=("Impact", 28, "bold"),
    fill="#FF4400"
)
# 3D shadow under title
header.create_text(
    312, 37,
    text="⛓  L I F E L O C K  ⛓",
    font=("Impact", 28, "bold"),
    fill="#330000"
)
header.create_text(
    310, 35,
    text="⛓  L I F E L O C K  ⛓",
    font=("Impact", 28, "bold"),
    fill="#FF4400"
)
header.create_text(
    310, 68,
    text="Y O U R   H A B I T S .   Y O U R   F U T U R E .   N O   E X C U S E S .",
    font=("Arial", 9),
    fill="#AA4400"
)

clock_label = tk.Label(
    root, text="",
    font=("Courier", 11),
    bg="#0a0a0a", fg="#AA4400"
)
clock_label.pack(pady=2)

# Divider
tk.Canvas(
    root, width=580, height=2,
    bg="#0a0a0a", highlightthickness=0
).pack()

# List frame with 3D border effect
list_outer = tk.Frame(root, bg="#FF2200", padx=1, pady=1)
list_outer.pack(padx=20, pady=8, fill="x")

list_inner = tk.Frame(list_outer, bg="#110000")
list_inner.pack(fill="both")

tk.Label(
    list_inner,
    text="  ◈  Y O U R   A C T I V I T I E S",
    font=("Arial", 10, "bold"),
    bg="#110000", fg="#FF4400", anchor="w"
).pack(fill="x", padx=10, pady=(6,2))

listbox = tk.Listbox(
    list_inner,
    font=("Courier", 11),
    bg="#1a0000", fg="#FF8888",
    selectbackground="#FF2200",
    selectforeground="white",
    height=8,
    borderwidth=0,
    highlightthickness=0
)
listbox.pack(fill="both", padx=8, pady=(0,8))

# Buttons with 3D raised effect
btn_frame = tk.Frame(root, bg="#0a0a0a")
btn_frame.pack(pady=8)

def make_3d_btn(parent, text, color, dark, cmd, r, c):
    f = tk.Frame(parent, bg=dark, padx=2, pady=2)
    f.grid(row=r, column=c, padx=6, pady=5)
    b = tk.Button(
        f, text=text,
        font=("Arial", 10, "bold"),
        bg=color, fg="white",
        activebackground=dark,
        width=17, height=2,
        borderwidth=0,
        cursor="hand2",
        command=cmd
    )
    b.pack()
    def on_e(e): b.config(bg=dark)
    def on_l(e): b.config(bg=color)
    b.bind("<Enter>", on_e)
    b.bind("<Leave>", on_l)
    return b

make_3d_btn(btn_frame, "➕  Add Activity",  "#228822","#115511", btn_add,       0, 0)
make_3d_btn(btn_frame, "✅  Mark Done",      "#224488","#112244", btn_mark_done, 0, 1)
make_3d_btn(btn_frame, "🔒  Test Lockdown", "#882222","#441111", btn_trigger_now,1, 0)
make_3d_btn(btn_frame, "🗑️  Delete",         "#664422","#332211", btn_delete,    1, 1)

# Status bar
status_outer = tk.Frame(root, bg="#FF2200", padx=1, pady=1)
status_outer.pack(fill="x", padx=20, pady=4)

status_label = tk.Label(
    status_outer,
    text="✅  All on track!  Apps unlocked.  🔓",
    font=("Courier", 10, "bold"),
    bg="#110000", fg="#44FF88",
    pady=7
)
status_label.pack(fill="x")

tk.Label(
    root,
    text="⊛  LifeLock is watching. Stay disciplined. 👁️  ⊛",
    font=("Arial", 9),
    bg="#0a0a0a", fg="#441100"
).pack(pady=(4, 10))

# ── START ────────────────────────────────────────────────
activities = load_activities()
refresh_list()
update_clock()

threading.Thread(target=background_monitor, daemon=True).start()

root.mainloop()