#!/usr/bin/env python3
"""GUI editor for Braitenberg vehicle simulation config JSON files."""

import json
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser

CONFIGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs")

FALLOFF_TYPES = ["inverse_square", "inverse_linear", "linear_gradient", "disk", "gaussian", "constant"]
FIELD_TYPES = ["temperature", "light", "chemical"]
RESPONSE_TYPES = ["linear", "threshold", "sigmoid", "logarithmic", "inverse", "bell", "triangular", "gaussian"]
SIDE_CHOICES = ["left", "right", "center"]
METHOD_CHOICES = ["euler", "arc"]

SKELETON = {
    "environment": {"fields": [{"type": "temperature", "sources": []}]},
    "sensors": {},
    "vehicles": [],
    "simulation": {"dt": 0.05, "method": "euler"},
    "view": {"center": [0, 0], "zoom": 1.0, "window_width": 1024, "window_height": 768},
    "colors": {},
}


def deep_copy(obj):
    return json.loads(json.dumps(obj))


class ConfigEditorApp(tk.Tk):
    def __init__(self, initial_path=None):
        super().__init__()
        self.title("Vehicle Config Editor")
        self.geometry("960x720")
        self.minsize(800, 600)

        self.data = None
        self.file_path = None
        self.dirty = False

        self._build_toolbar()
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w").pack(
            fill="x", side="bottom", padx=6, pady=(0, 4)
        )

        # Keyboard shortcuts
        mod = "Command" if sys.platform == "darwin" else "Control"
        self.bind(f"<{mod}-o>", lambda e: self.open_config())
        self.bind(f"<{mod}-s>", lambda e: self.save_config())
        self.bind(f"<{mod}-Shift-s>", lambda e: self.save_config_as())
        self.bind(f"<{mod}-n>", lambda e: self.new_config())
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        if initial_path:
            self._load_file(initial_path)
        else:
            self.new_config()

    # ── Toolbar ──────────────────────────────────────────────
    def _build_toolbar(self):
        tb = ttk.Frame(self)
        tb.pack(fill="x", padx=6, pady=6)
        ttk.Button(tb, text="New", command=self.new_config).pack(side="left", padx=2)
        ttk.Button(tb, text="Open...", command=self.open_config).pack(side="left", padx=2)
        ttk.Button(tb, text="Save", command=self.save_config).pack(side="left", padx=2)
        ttk.Button(tb, text="Save As...", command=self.save_config_as).pack(side="left", padx=2)
        ttk.Separator(tb, orient="vertical").pack(side="left", fill="y", padx=8)
        self.file_label = ttk.Label(tb, text="(no file)", foreground="gray")
        self.file_label.pack(side="left", padx=4)

    # ── File I/O ─────────────────────────────────────────────
    def _confirm_discard(self):
        if self.dirty:
            return messagebox.askyesnocancel("Unsaved Changes", "You have unsaved changes. Discard them?")
        return True

    def new_config(self):
        r = self._confirm_discard()
        if r is None or r is False:
            return
        self.data = deep_copy(SKELETON)
        self.file_path = None
        self.dirty = False
        self._rebuild_tabs()
        self._update_title()
        self.file_label.config(text="(new config)")
        self.status_var.set("New config created")

    def open_config(self):
        r = self._confirm_discard()
        if r is None or r is False:
            return
        path = filedialog.askopenfilename(
            initialdir=CONFIGS_DIR, filetypes=[("JSON files", "*.json"), ("All", "*.*")]
        )
        if path:
            self._load_file(path)

    def _load_file(self, path):
        try:
            with open(path) as f:
                self.data = json.load(f)
        except Exception as e:
            messagebox.showerror("Load Error", str(e))
            return
        self.file_path = path
        self.dirty = False
        self._rebuild_tabs()
        self._update_title()
        self.file_label.config(text=os.path.basename(path))
        self.status_var.set(f"Loaded {os.path.basename(path)}")

    def save_config(self):
        if self.file_path is None:
            self.save_config_as()
            return
        self._write_file(self.file_path)

    def save_config_as(self):
        path = filedialog.asksaveasfilename(
            initialdir=CONFIGS_DIR,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
        )
        if path:
            self._write_file(path)
            self.file_path = path
            self.file_label.config(text=os.path.basename(path))
            self._update_title()

    def _write_file(self, path):
        try:
            with open(path, "w") as f:
                json.dump(self.data, f, indent=2)
                f.write("\n")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))
            return
        self.dirty = False
        self._update_title()
        self.status_var.set(f"Saved {os.path.basename(path)}")

    def mark_dirty(self):
        self.dirty = True
        self._update_title()

    def _update_title(self):
        name = os.path.basename(self.file_path) if self.file_path else "New Config"
        prefix = "* " if self.dirty else ""
        self.title(f"{prefix}{name} — Vehicle Config Editor")

    def on_close(self):
        r = self._confirm_discard()
        if r is None or r is False:
            return
        self.destroy()

    # ── Tab Management ───────────────────────────────────────
    def _rebuild_tabs(self):
        for tab in self.notebook.tabs():
            self.notebook.forget(tab)
        self.notebook.add(EnvironmentTab(self.notebook, self), text="Environment")
        self.notebook.add(SensorsTab(self.notebook, self), text="Sensors")
        self.notebook.add(VehiclesTab(self.notebook, self), text="Vehicles")
        self.notebook.add(SimulationTab(self.notebook, self), text="Simulation")
        self.notebook.add(ViewTab(self.notebook, self), text="View")
        self.notebook.add(ColorsTab(self.notebook, self), text="Colors")
        self.notebook.add(JsonTab(self.notebook, self), text="JSON")


# ═══════════════════════════════════════════════════════════
# Helper: reusable list editor (listbox + add/remove/dup)
# ═══════════════════════════════════════════════════════════
class ListEditor(ttk.Frame):
    """Listbox with Add/Remove/Duplicate/Move buttons. Calls on_select(index) when selection changes."""

    def __init__(self, parent, app, items_ref_fn, label_fn, new_item_fn, on_select, title="Items"):
        super().__init__(parent)
        self.app = app
        self.items_ref_fn = items_ref_fn  # callable -> returns the list
        self.label_fn = label_fn
        self.new_item_fn = new_item_fn
        self.on_select_cb = on_select

        ttk.Label(self, text=title, font=("TkDefaultFont", 11, "bold")).pack(anchor="w")
        self.listbox = tk.Listbox(self, width=28, exportselection=False)
        self.listbox.pack(fill="both", expand=True, pady=(2, 4))
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x")
        ttk.Button(btn_frame, text="+", width=3, command=self.add_item).pack(side="left", padx=1)
        ttk.Button(btn_frame, text="-", width=3, command=self.remove_item).pack(side="left", padx=1)
        ttk.Button(btn_frame, text="Dup", width=4, command=self.dup_item).pack(side="left", padx=1)
        ttk.Button(btn_frame, text="\u25b2", width=3, command=lambda: self.move(-1)).pack(side="left", padx=1)
        ttk.Button(btn_frame, text="\u25bc", width=3, command=lambda: self.move(1)).pack(side="left", padx=1)

    def refresh(self, select_index=None):
        self.listbox.delete(0, "end")
        items = self.items_ref_fn()
        for i, item in enumerate(items):
            self.listbox.insert("end", self.label_fn(i, item))
        if select_index is not None and 0 <= select_index < len(items):
            self.listbox.selection_set(select_index)
            self.listbox.see(select_index)
            self.on_select_cb(select_index)
        elif items:
            self.listbox.selection_set(0)
            self.on_select_cb(0)
        else:
            self.on_select_cb(-1)

    def _on_select(self, event=None):
        sel = self.listbox.curselection()
        if sel:
            self.on_select_cb(sel[0])

    def selected_index(self):
        sel = self.listbox.curselection()
        return sel[0] if sel else -1

    def add_item(self):
        items = self.items_ref_fn()
        items.append(self.new_item_fn())
        self.app.mark_dirty()
        self.refresh(select_index=len(items) - 1)

    def remove_item(self):
        idx = self.selected_index()
        items = self.items_ref_fn()
        if idx < 0 or idx >= len(items):
            return
        items.pop(idx)
        self.app.mark_dirty()
        self.refresh(select_index=min(idx, len(items) - 1))

    def dup_item(self):
        idx = self.selected_index()
        items = self.items_ref_fn()
        if idx < 0 or idx >= len(items):
            return
        items.append(deep_copy(items[idx]))
        self.app.mark_dirty()
        self.refresh(select_index=len(items) - 1)

    def move(self, delta):
        idx = self.selected_index()
        items = self.items_ref_fn()
        new_idx = idx + delta
        if idx < 0 or new_idx < 0 or new_idx >= len(items):
            return
        items[idx], items[new_idx] = items[new_idx], items[idx]
        self.app.mark_dirty()
        self.refresh(select_index=new_idx)


# ═══════════════════════════════════════════════════════════
# Helper: form builder
# ═══════════════════════════════════════════════════════════
class FormBuilder:
    """Builds labeled form rows in a grid frame."""

    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.row = 0
        self.widgets = {}

    def add_float(self, key, label, value, **kw):
        ttk.Label(self.parent, text=label).grid(row=self.row, column=0, sticky="e", padx=(0, 6), pady=2)
        var = tk.DoubleVar(value=value)
        entry = ttk.Entry(self.parent, textvariable=var, width=14)
        entry.grid(row=self.row, column=1, sticky="w", pady=2)
        var.trace_add("write", lambda *a: self.app.mark_dirty())
        self.widgets[key] = var
        self.row += 1
        return var

    def add_int(self, key, label, value, **kw):
        ttk.Label(self.parent, text=label).grid(row=self.row, column=0, sticky="e", padx=(0, 6), pady=2)
        var = tk.IntVar(value=value)
        sb = ttk.Spinbox(self.parent, textvariable=var, from_=kw.get("from_", 0), to=kw.get("to", 9999), width=12)
        sb.grid(row=self.row, column=1, sticky="w", pady=2)
        var.trace_add("write", lambda *a: self.app.mark_dirty())
        self.widgets[key] = var
        self.row += 1
        return var

    def add_str(self, key, label, value):
        ttk.Label(self.parent, text=label).grid(row=self.row, column=0, sticky="e", padx=(0, 6), pady=2)
        var = tk.StringVar(value=value)
        entry = ttk.Entry(self.parent, textvariable=var, width=20)
        entry.grid(row=self.row, column=1, sticky="w", pady=2)
        var.trace_add("write", lambda *a: self.app.mark_dirty())
        self.widgets[key] = var
        self.row += 1
        return var

    def add_enum(self, key, label, value, choices):
        ttk.Label(self.parent, text=label).grid(row=self.row, column=0, sticky="e", padx=(0, 6), pady=2)
        var = tk.StringVar(value=value)
        cb = ttk.Combobox(self.parent, textvariable=var, values=choices, state="readonly", width=18)
        cb.grid(row=self.row, column=1, sticky="w", pady=2)
        var.trace_add("write", lambda *a: self.app.mark_dirty())
        self.widgets[key] = var
        self.row += 1
        return var

    def add_point(self, key, label, x_val, y_val):
        ttk.Label(self.parent, text=label).grid(row=self.row, column=0, sticky="e", padx=(0, 6), pady=2)
        frame = ttk.Frame(self.parent)
        frame.grid(row=self.row, column=1, sticky="w", pady=2)
        x_var = tk.DoubleVar(value=x_val)
        y_var = tk.DoubleVar(value=y_val)
        ttk.Label(frame, text="x:").pack(side="left")
        ttk.Entry(frame, textvariable=x_var, width=8).pack(side="left", padx=(0, 6))
        ttk.Label(frame, text="y:").pack(side="left")
        ttk.Entry(frame, textvariable=y_var, width=8).pack(side="left")
        x_var.trace_add("write", lambda *a: self.app.mark_dirty())
        y_var.trace_add("write", lambda *a: self.app.mark_dirty())
        self.widgets[key + "_x"] = x_var
        self.widgets[key + "_y"] = y_var
        self.row += 1
        return x_var, y_var

    def add_bool(self, key, label, value):
        var = tk.BooleanVar(value=value)
        cb = ttk.Checkbutton(self.parent, text=label, variable=var)
        cb.grid(row=self.row, column=0, columnspan=2, sticky="w", pady=2)
        var.trace_add("write", lambda *a: self.app.mark_dirty())
        self.widgets[key] = var
        self.row += 1
        return var


# ═══════════════════════════════════════════════════════════
# Environment Tab
# ═══════════════════════════════════════════════════════════
class EnvironmentTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=8)
        self.app = app
        self.data = app.data

        pane = ttk.PanedWindow(self, orient="horizontal")
        pane.pack(fill="both", expand=True)

        # Left: fields list + sources list
        left = ttk.Frame(pane)
        pane.add(left, weight=1)

        self.field_list = ListEditor(
            left, app,
            items_ref_fn=lambda: self.data["environment"]["fields"],
            label_fn=lambda i, f: f"Field {i}: {f.get('type', '?')}",
            new_item_fn=lambda: {"type": "temperature", "sources": []},
            on_select=self._on_field_select,
            title="Fields",
        )
        self.field_list.pack(fill="both", expand=True)

        self.source_list = ListEditor(
            left, app,
            items_ref_fn=self._current_sources,
            label_fn=lambda i, s: f"Src {i}: ({s['position'][0]}, {s['position'][1]})",
            new_item_fn=lambda: {"position": [0, 0], "intensity": 1000, "radius": 5, "falloff": "inverse_square"},
            on_select=self._on_source_select,
            title="Sources",
        )
        self.source_list.pack(fill="both", expand=True, pady=(8, 0))

        # Right: detail panel
        self.detail = ttk.Frame(pane, padding=8)
        pane.add(self.detail, weight=2)

        self.sel_field = -1
        self.sel_source = -1
        self.field_list.refresh()

    def _current_field(self):
        fields = self.data["environment"]["fields"]
        if 0 <= self.sel_field < len(fields):
            return fields[self.sel_field]
        return None

    def _current_sources(self):
        f = self._current_field()
        return f["sources"] if f else []

    def _on_field_select(self, idx):
        self.sel_field = idx
        f = self._current_field()
        self._clear_detail()
        if f is None:
            self.source_list.refresh()
            return
        # Field type selector
        ttk.Label(self.detail, text="Field Type:", font=("TkDefaultFont", 11, "bold")).grid(row=0, column=0, sticky="e", padx=(0, 6))
        ft_var = tk.StringVar(value=f.get("type", "temperature"))
        cb = ttk.Combobox(self.detail, textvariable=ft_var, values=FIELD_TYPES, width=18)
        cb.grid(row=0, column=1, sticky="w")
        ft_var.trace_add("write", lambda *a: self._set_field_val("type", ft_var.get()))
        ttk.Separator(self.detail, orient="horizontal").grid(row=1, column=0, columnspan=2, sticky="ew", pady=8)
        self.source_list.refresh()

    def _on_source_select(self, idx):
        self.sel_source = idx
        # Clear detail rows below the field-type section (row >= 2)
        for w in self.detail.grid_slaves():
            if int(w.grid_info()["row"]) >= 2:
                w.destroy()

        sources = self._current_sources()
        if idx < 0 or idx >= len(sources):
            return
        s = sources[idx]

        frame = ttk.Frame(self.detail)
        frame.grid(row=2, column=0, columnspan=2, sticky="nsew")
        fb = FormBuilder(frame, self.app)
        fb.add_point("pos", "Position:", s["position"][0], s["position"][1])
        fb.add_float("intensity", "Intensity:", s.get("intensity", 0))
        fb.add_float("radius", "Radius:", s.get("radius", 0))
        fb.add_enum("falloff", "Falloff:", s.get("falloff", "inverse_square"), FALLOFF_TYPES)
        fb.add_float("sigma", "Sigma:", s.get("sigma", 1.0))
        fb.add_float("cutoff_radius", "Cutoff Radius:", s.get("cutoff_radius", 0.0))

        def write_back(*a):
            try:
                s["position"] = [fb.widgets["pos_x"].get(), fb.widgets["pos_y"].get()]
                s["intensity"] = fb.widgets["intensity"].get()
                s["radius"] = fb.widgets["radius"].get()
                s["falloff"] = fb.widgets["falloff"].get()
                s["sigma"] = fb.widgets["sigma"].get()
                s["cutoff_radius"] = fb.widgets["cutoff_radius"].get()
            except (tk.TclError, ValueError):
                pass

        for var in fb.widgets.values():
            var.trace_add("write", write_back)

    def _set_field_val(self, key, val):
        f = self._current_field()
        if f:
            f[key] = val
            self.app.mark_dirty()
            self.field_list.refresh(select_index=self.sel_field)

    def _clear_detail(self):
        for w in self.detail.winfo_children():
            w.destroy()


# ═══════════════════════════════════════════════════════════
# Sensors Tab
# ═══════════════════════════════════════════════════════════
class SensorsTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=8)
        self.app = app
        self.data = app.data

        pane = ttk.PanedWindow(self, orient="horizontal")
        pane.pack(fill="both", expand=True)

        left = ttk.Frame(pane)
        pane.add(left, weight=1)

        ttk.Label(left, text="Sensor Definitions", font=("TkDefaultFont", 11, "bold")).pack(anchor="w")
        self.listbox = tk.Listbox(left, width=24, exportselection=False)
        self.listbox.pack(fill="both", expand=True, pady=(2, 4))
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill="x")
        ttk.Button(btn_frame, text="Add", command=self._add).pack(side="left", padx=1)
        ttk.Button(btn_frame, text="Remove", command=self._remove).pack(side="left", padx=1)
        ttk.Button(btn_frame, text="Duplicate", command=self._dup).pack(side="left", padx=1)

        self.detail = ttk.Frame(pane, padding=8)
        pane.add(self.detail, weight=2)

        self._refresh()

    def _sensor_names(self):
        return list(self.data.get("sensors", {}).keys())

    def _refresh(self, select_name=None):
        self.listbox.delete(0, "end")
        names = self._sensor_names()
        for n in names:
            self.listbox.insert("end", n)
        if select_name and select_name in names:
            idx = names.index(select_name)
            self.listbox.selection_set(idx)
            self._show_detail(select_name)
        elif names:
            self.listbox.selection_set(0)
            self._show_detail(names[0])
        else:
            self._clear_detail()

    def _selected_name(self):
        sel = self.listbox.curselection()
        if sel:
            return self.listbox.get(sel[0])
        return None

    def _on_select(self, event=None):
        name = self._selected_name()
        if name:
            self._show_detail(name)

    def _add(self):
        i = len(self.data.get("sensors", {}))
        name = f"sensor-{i}"
        while name in self.data["sensors"]:
            i += 1
            name = f"sensor-{i}"
        self.data["sensors"][name] = {
            "stimulus_unit": "K",
            "response_function": {"type": "bell", "peak_stimulus": 100, "max_voltage": 50},
        }
        self.app.mark_dirty()
        self._refresh(select_name=name)

    def _remove(self):
        name = self._selected_name()
        if name:
            del self.data["sensors"][name]
            self.app.mark_dirty()
            self._refresh()

    def _dup(self):
        name = self._selected_name()
        if not name:
            return
        new_name = name + "_copy"
        self.data["sensors"][new_name] = deep_copy(self.data["sensors"][name])
        self.app.mark_dirty()
        self._refresh(select_name=new_name)

    def _show_detail(self, name):
        self._clear_detail()
        sd = self.data["sensors"][name]
        rf = sd.get("response_function", {})

        fb = FormBuilder(self.detail, self.app)

        name_var = fb.add_str("name", "Name:", name)
        fb.add_str("unit", "Stimulus Unit:", sd.get("stimulus_unit", "K"))

        ttk.Separator(self.detail).grid(row=fb.row, column=0, columnspan=2, sticky="ew", pady=8)
        fb.row += 1
        ttk.Label(self.detail, text="Response Function", font=("TkDefaultFont", 10, "bold")).grid(
            row=fb.row, column=0, columnspan=2, sticky="w"
        )
        fb.row += 1

        fb.add_enum("rf_type", "Type:", rf.get("type", "bell"), RESPONSE_TYPES)
        fb.add_float("gain", "Gain:", rf.get("gain", 1.0))
        fb.add_float("threshold", "Threshold:", rf.get("threshold", 0.0))
        fb.add_float("midpoint", "Midpoint:", rf.get("midpoint", 0.0))
        fb.add_float("max_voltage", "Max Voltage:", rf.get("max_voltage", 10.0))
        fb.add_float("peak_stimulus", "Peak Stimulus:", rf.get("peak_stimulus", 100.0))
        fb.add_float("sigma", "Sigma:", rf.get("sigma", 0.0))
        fb.add_float("output_bias", "Output Bias:", rf.get("output_bias", 0.0))

        def write_back(*a):
            try:
                new_name = fb.widgets["name"].get().strip()
                sd["stimulus_unit"] = fb.widgets["unit"].get()
                rf["type"] = fb.widgets["rf_type"].get()
                rf["gain"] = fb.widgets["gain"].get()
                rf["threshold"] = fb.widgets["threshold"].get()
                rf["midpoint"] = fb.widgets["midpoint"].get()
                rf["max_voltage"] = fb.widgets["max_voltage"].get()
                rf["peak_stimulus"] = fb.widgets["peak_stimulus"].get()
                rf["sigma"] = fb.widgets["sigma"].get()
                rf["output_bias"] = fb.widgets["output_bias"].get()
                sd["response_function"] = rf
                # Handle rename
                if new_name and new_name != name:
                    self._rename_sensor(name, new_name)
            except (tk.TclError, ValueError):
                pass

        for var in fb.widgets.values():
            var.trace_add("write", write_back)

    def _rename_sensor(self, old, new):
        if new in self.data["sensors"]:
            return  # don't overwrite
        self.data["sensors"][new] = self.data["sensors"].pop(old)
        # Update vehicle references
        for v in self.data.get("vehicles", []):
            for m in v.get("sensor_mounts", []):
                if m.get("sensor") == old:
                    m["sensor"] = new
        self.app.mark_dirty()
        self._refresh(select_name=new)

    def _clear_detail(self):
        for w in self.detail.winfo_children():
            w.destroy()


# ═══════════════════════════════════════════════════════════
# Vehicles Tab
# ═══════════════════════════════════════════════════════════
class VehiclesTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=8)
        self.app = app
        self.data = app.data

        pane = ttk.PanedWindow(self, orient="horizontal")
        pane.pack(fill="both", expand=True)

        left = ttk.Frame(pane)
        pane.add(left, weight=1)

        self.veh_list = ListEditor(
            left, app,
            items_ref_fn=lambda: self.data["vehicles"],
            label_fn=lambda i, v: v.get("name", f"vehicle-{i}"),
            new_item_fn=lambda: {
                "name": "new-vehicle",
                "position": [100, 100],
                "heading": 0.0,
                "body_radius": 8,
                "axle_width": 12,
                "sensor_mounts": [],
                "motors": [
                    {"id": "ML", "side": "left", "max_speed": 80.0, "gain": 1.0, "base_voltage": 0.0},
                    {"id": "MR", "side": "right", "max_speed": 80.0, "gain": 1.0, "base_voltage": 0.0},
                ],
                "connections": [],
            },
            on_select=self._on_vehicle_select,
            title="Vehicles",
        )
        self.veh_list.pack(fill="both", expand=True)

        self.detail = ttk.Frame(pane, padding=8)
        pane.add(self.detail, weight=3)

        self.sel_veh = -1
        self.veh_list.refresh()

    def _current_vehicle(self):
        vehs = self.data["vehicles"]
        if 0 <= self.sel_veh < len(vehs):
            return vehs[self.sel_veh]
        return None

    def _on_vehicle_select(self, idx):
        self.sel_veh = idx
        for w in self.detail.winfo_children():
            w.destroy()
        v = self._current_vehicle()
        if v is None:
            return

        # Top fields
        top = ttk.Frame(self.detail)
        top.pack(fill="x")
        fb = FormBuilder(top, self.app)
        fb.add_str("name", "Name:", v.get("name", ""))
        fb.add_point("pos", "Position:", v["position"][0], v["position"][1])
        fb.add_float("heading", "Heading (rad):", v.get("heading", 0.0))
        fb.add_float("body_radius", "Body Radius:", v.get("body_radius", 8))
        fb.add_float("axle_width", "Axle Width:", v.get("axle_width", 12))
        fb.add_bool("enabled", "Enabled", v.get("enabled", True))

        def write_top(*a):
            try:
                v["name"] = fb.widgets["name"].get()
                v["position"] = [fb.widgets["pos_x"].get(), fb.widgets["pos_y"].get()]
                v["heading"] = fb.widgets["heading"].get()
                v["body_radius"] = fb.widgets["body_radius"].get()
                v["axle_width"] = fb.widgets["axle_width"].get()
                v["enabled"] = fb.widgets["enabled"].get()
            except (tk.TclError, ValueError):
                pass

        for var in fb.widgets.values():
            var.trace_add("write", write_top)

        # Sub-notebook for mounts, motors, connections
        sub_nb = ttk.Notebook(self.detail)
        sub_nb.pack(fill="both", expand=True, pady=(8, 0))
        sub_nb.add(self._build_mounts_tab(sub_nb, v), text="Sensor Mounts")
        sub_nb.add(self._build_motors_tab(sub_nb, v), text="Motors")
        sub_nb.add(self._build_connections_tab(sub_nb, v), text="Connections")

    def _build_mounts_tab(self, parent, vehicle):
        frame = ttk.Frame(parent, padding=4)
        pane = ttk.PanedWindow(frame, orient="horizontal")
        pane.pack(fill="both", expand=True)

        detail = ttk.Frame(pane, padding=4)

        sensor_names = list(self.data.get("sensors", {}).keys())

        def show_mount(idx):
            for w in detail.winfo_children():
                w.destroy()
            mounts = vehicle.get("sensor_mounts", [])
            if idx < 0 or idx >= len(mounts):
                return
            m = mounts[idx]
            fb = FormBuilder(detail, self.app)
            fb.add_str("id", "ID:", m.get("id", ""))
            fb.add_enum("sensor", "Sensor:", m.get("sensor", ""), sensor_names or [""])
            fb.add_enum("side", "Side:", m.get("side", "left"), SIDE_CHOICES)
            fb.add_float("angle_offset", "Angle Offset (rad):", m.get("angle_offset", 0.0))
            ttk.Label(detail, text="0=front, \u00b1\u03c0/2=sides, \u03c0=rear", foreground="gray").grid(
                row=fb.row, column=0, columnspan=2, sticky="w", padx=(4, 0))
            fb.row += 1
            fb.add_float("dist", "Distance:", m.get("distance_from_center", 8))

            def wb(*a):
                try:
                    m["id"] = fb.widgets["id"].get()
                    m["sensor"] = fb.widgets["sensor"].get()
                    m["side"] = fb.widgets["side"].get()
                    m["angle_offset"] = fb.widgets["angle_offset"].get()
                    m["distance_from_center"] = fb.widgets["dist"].get()
                except (tk.TclError, ValueError):
                    pass
            for var in fb.widgets.values():
                var.trace_add("write", wb)

        le = ListEditor(
            pane, self.app,
            items_ref_fn=lambda: vehicle.setdefault("sensor_mounts", []),
            label_fn=lambda i, m: m.get("id", f"mount-{i}"),
            new_item_fn=lambda: {"id": f"S{len(vehicle.get('sensor_mounts', []))}", "sensor": sensor_names[0] if sensor_names else "", "side": "left", "angle_offset": 0.0, "distance_from_center": 8},
            on_select=show_mount,
            title="Mounts",
        )
        pane.add(le, weight=1)
        pane.add(detail, weight=2)
        le.refresh()
        return frame

    def _build_motors_tab(self, parent, vehicle):
        frame = ttk.Frame(parent, padding=4)
        pane = ttk.PanedWindow(frame, orient="horizontal")
        pane.pack(fill="both", expand=True)

        detail = ttk.Frame(pane, padding=4)

        def show_motor(idx):
            for w in detail.winfo_children():
                w.destroy()
            motors = vehicle.get("motors", [])
            if idx < 0 or idx >= len(motors):
                return
            m = motors[idx]
            fb = FormBuilder(detail, self.app)
            fb.add_str("id", "ID:", m.get("id", ""))
            fb.add_enum("side", "Side:", m.get("side", "left"), ["left", "right"])
            fb.add_float("gain", "Gain:", m.get("gain", 1.0))
            fb.add_float("max_speed", "Max Speed:", m.get("max_speed", 80.0))
            fb.add_float("base_voltage", "Base Voltage:", m.get("base_voltage", 0.0))

            def wb(*a):
                try:
                    m["id"] = fb.widgets["id"].get()
                    m["side"] = fb.widgets["side"].get()
                    m["gain"] = fb.widgets["gain"].get()
                    m["max_speed"] = fb.widgets["max_speed"].get()
                    m["base_voltage"] = fb.widgets["base_voltage"].get()
                except (tk.TclError, ValueError):
                    pass
            for var in fb.widgets.values():
                var.trace_add("write", wb)

        le = ListEditor(
            pane, self.app,
            items_ref_fn=lambda: vehicle.setdefault("motors", []),
            label_fn=lambda i, m: f"{m.get('id', '?')} ({m.get('side', '?')})",
            new_item_fn=lambda: {"id": f"M{len(vehicle.get('motors', []))}", "side": "left", "max_speed": 80.0, "gain": 1.0, "base_voltage": 0.0},
            on_select=show_motor,
            title="Motors",
        )
        pane.add(le, weight=1)
        pane.add(detail, weight=2)
        le.refresh()
        return frame

    def _build_connections_tab(self, parent, vehicle):
        frame = ttk.Frame(parent, padding=4)
        pane = ttk.PanedWindow(frame, orient="horizontal")
        pane.pack(fill="both", expand=True)

        detail = ttk.Frame(pane, padding=4)

        def sensor_ids():
            return [m.get("id", "") for m in vehicle.get("sensor_mounts", [])] or [""]

        def motor_ids():
            return [m.get("id", "") for m in vehicle.get("motors", [])] or [""]

        def show_conn(idx):
            for w in detail.winfo_children():
                w.destroy()
            conns = vehicle.get("connections", [])
            if idx < 0 or idx >= len(conns):
                return
            c = conns[idx]
            fb = FormBuilder(detail, self.app)
            fb.add_enum("from", "From Sensor:", c.get("from_sensor", ""), sensor_ids())
            fb.add_enum("to", "To Motor:", c.get("to_motor", ""), motor_ids())
            fb.add_float("weight", "Weight:", c.get("weight", 1.0))

            def wb(*a):
                try:
                    c["from_sensor"] = fb.widgets["from"].get()
                    c["to_motor"] = fb.widgets["to"].get()
                    c["weight"] = fb.widgets["weight"].get()
                except (tk.TclError, ValueError):
                    pass
            for var in fb.widgets.values():
                var.trace_add("write", wb)

        le = ListEditor(
            pane, self.app,
            items_ref_fn=lambda: vehicle.setdefault("connections", []),
            label_fn=lambda i, c: f"{c.get('from_sensor', '?')} -> {c.get('to_motor', '?')} ({c.get('weight', 0)})",
            new_item_fn=lambda: {"from_sensor": sensor_ids()[0], "to_motor": motor_ids()[0], "weight": 1.0},
            on_select=show_conn,
            title="Connections",
        )
        pane.add(le, weight=1)
        pane.add(detail, weight=2)
        le.refresh()
        return frame


# ═══════════════════════════════════════════════════════════
# Simulation Tab
# ═══════════════════════════════════════════════════════════
class SimulationTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=16)
        self.app = app
        sim = app.data.setdefault("simulation", {"dt": 0.05, "method": "euler"})

        fb = FormBuilder(self, app)
        fb.add_float("dt", "Time Step (dt):", sim.get("dt", 0.05))
        fb.add_enum("method", "Method:", sim.get("method", "euler"), METHOD_CHOICES)

        def write_back(*a):
            try:
                sim["dt"] = fb.widgets["dt"].get()
                sim["method"] = fb.widgets["method"].get()
            except (tk.TclError, ValueError):
                pass

        for var in fb.widgets.values():
            var.trace_add("write", write_back)


# ═══════════════════════════════════════════════════════════
# View Tab
# ═══════════════════════════════════════════════════════════
class ViewTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=16)
        self.app = app
        vw = app.data.setdefault("view", {"center": [0, 0], "zoom": 1.0, "window_width": 1024, "window_height": 768})

        fb = FormBuilder(self, app)
        fb.add_point("center", "Center:", vw.get("center", [0, 0])[0], vw.get("center", [0, 0])[1])
        fb.add_float("zoom", "Zoom:", vw.get("zoom", 1.0))
        fb.add_int("width", "Window Width:", vw.get("window_width", 1024), from_=320, to=3840)
        fb.add_int("height", "Window Height:", vw.get("window_height", 768), from_=240, to=2160)

        def write_back(*a):
            try:
                vw["center"] = [fb.widgets["center_x"].get(), fb.widgets["center_y"].get()]
                vw["zoom"] = fb.widgets["zoom"].get()
                vw["window_width"] = fb.widgets["width"].get()
                vw["window_height"] = fb.widgets["height"].get()
            except (tk.TclError, ValueError):
                pass

        for var in fb.widgets.values():
            var.trace_add("write", write_back)


# ═══════════════════════════════════════════════════════════
# Colors Tab
# ═══════════════════════════════════════════════════════════
class ColorsTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=16)
        self.app = app
        self.data = app.data

        top = ttk.Frame(self)
        top.pack(fill="x")
        ttk.Label(top, text="Field Colors", font=("TkDefaultFont", 11, "bold")).pack(side="left")
        ttk.Button(top, text="Add", command=self._add).pack(side="right", padx=2)

        self.tree = ttk.Treeview(self, columns=("r", "g", "b"), show="headings", height=6)
        self.tree.heading("#0", text="Type")
        self.tree.heading("r", text="R")
        self.tree.heading("g", text="G")
        self.tree.heading("b", text="B")
        self.tree.column("r", width=60, anchor="center")
        self.tree.column("g", width=60, anchor="center")
        self.tree.column("b", width=60, anchor="center")
        self.tree.pack(fill="both", expand=True, pady=4)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        self.edit_frame = ttk.Frame(self)
        self.edit_frame.pack(fill="x", pady=4)

        self._refresh()

    def _refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        colors = self.data.get("colors", {})
        for name, rgb in colors.items():
            self.tree.insert("", "end", iid=name, text=name, values=(rgb[0], rgb[1], rgb[2]))
            # Use treeview text column
        # Re-configure to show tree column for the name
        self.tree["show"] = ("tree", "headings")
        self.tree.heading("#0", text="Field Type")
        self.tree.column("#0", width=140)

    def _on_select(self, event=None):
        for w in self.edit_frame.winfo_children():
            w.destroy()
        sel = self.tree.selection()
        if not sel:
            return
        name = sel[0]
        rgb = self.data["colors"][name]

        ttk.Label(self.edit_frame, text="R:").pack(side="left")
        r_var = tk.IntVar(value=rgb[0])
        ttk.Spinbox(self.edit_frame, textvariable=r_var, from_=0, to=255, width=5).pack(side="left", padx=(0, 8))
        ttk.Label(self.edit_frame, text="G:").pack(side="left")
        g_var = tk.IntVar(value=rgb[1])
        ttk.Spinbox(self.edit_frame, textvariable=g_var, from_=0, to=255, width=5).pack(side="left", padx=(0, 8))
        ttk.Label(self.edit_frame, text="B:").pack(side="left")
        b_var = tk.IntVar(value=rgb[2])
        ttk.Spinbox(self.edit_frame, textvariable=b_var, from_=0, to=255, width=5).pack(side="left", padx=(0, 8))

        self.swatch = tk.Canvas(self.edit_frame, width=30, height=30, bd=1, relief="sunken")
        self.swatch.pack(side="left", padx=8)
        self._update_swatch(rgb)

        ttk.Button(self.edit_frame, text="Pick...", command=lambda: self._pick_color(name, r_var, g_var, b_var)).pack(side="left", padx=4)
        ttk.Button(self.edit_frame, text="Remove", command=lambda: self._remove(name)).pack(side="left", padx=4)

        def wb(*a):
            try:
                self.data["colors"][name] = [r_var.get(), g_var.get(), b_var.get()]
                self._update_swatch(self.data["colors"][name])
                self.app.mark_dirty()
            except (tk.TclError, ValueError):
                pass

        r_var.trace_add("write", wb)
        g_var.trace_add("write", wb)
        b_var.trace_add("write", wb)

    def _update_swatch(self, rgb):
        color = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
        self.swatch.delete("all")
        self.swatch.create_rectangle(0, 0, 30, 30, fill=color, outline="")

    def _pick_color(self, name, r_var, g_var, b_var):
        rgb = self.data["colors"][name]
        result = colorchooser.askcolor(initialcolor=f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}")
        if result and result[0]:
            r, g, b = [int(c) for c in result[0]]
            r_var.set(r)
            g_var.set(g)
            b_var.set(b)

    def _add(self):
        name = "temperature"
        if name in self.data.setdefault("colors", {}):
            for ft in FIELD_TYPES:
                if ft not in self.data["colors"]:
                    name = ft
                    break
        self.data["colors"][name] = [255, 255, 255]
        self.app.mark_dirty()
        self._refresh()

    def _remove(self, name):
        if name in self.data.get("colors", {}):
            del self.data["colors"][name]
            self.app.mark_dirty()
            self._refresh()


# ═══════════════════════════════════════════════════════════
# JSON Preview Tab
# ═══════════════════════════════════════════════════════════
class JsonTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=8)
        self.app = app

        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 4))
        ttk.Button(top, text="Refresh", command=self._refresh).pack(side="left")
        ttk.Button(top, text="Copy to Clipboard", command=self._copy).pack(side="left", padx=8)
        ttk.Button(top, text="Apply Edits", command=self._apply).pack(side="left", padx=4)

        self.text = tk.Text(self, wrap="none", font=("Menlo", 11))
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.text.xview)
        self.text.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.text.pack(fill="both", expand=True)

        self._refresh()

    def _refresh(self):
        self.text.delete("1.0", "end")
        self.text.insert("1.0", json.dumps(self.app.data, indent=2))

    def _copy(self):
        self.clipboard_clear()
        self.clipboard_append(json.dumps(self.app.data, indent=2))
        self.app.status_var.set("JSON copied to clipboard")

    def _apply(self):
        try:
            new_data = json.loads(self.text.get("1.0", "end"))
        except json.JSONDecodeError as e:
            messagebox.showerror("Invalid JSON", str(e))
            return
        self.app.data.clear()
        self.app.data.update(new_data)
        self.app.mark_dirty()
        self.app._rebuild_tabs()
        self.app.status_var.set("Applied JSON edits")


# ═══════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    app = ConfigEditorApp(initial_path=path)
    app.mainloop()
