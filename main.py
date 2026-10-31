import json
import random
from pathlib import Path
from datetime import datetime, timedelta

from kivy.app import App
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Line, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.checkbox import CheckBox
from kivy.uix.widget import Widget


APP_NAME = "Mevira Keep"
DATA_FILE = Path.home() / "mevira_keep_notes.json"

Window.clearcolor = (0.94, 0.95, 0.97, 1)

NOTE_COLORS = [
    ("Default", [1.00, 1.00, 1.00, 1]),
    ("Rose", [1.00, 0.86, 0.87, 1]),
    ("Peach", [1.00, 0.90, 0.78, 1]),
    ("Sand", [0.98, 0.94, 0.78, 1]),
    ("Mint", [0.82, 0.94, 0.86, 1]),
    ("Sky", [0.80, 0.91, 0.99, 1]),
    ("Lavender", [0.89, 0.85, 0.98, 1]),
    ("Grey", [0.88, 0.90, 0.92, 1]),
]

QUOTES = [
    "“The secret of getting ahead is getting started.” – Mark Twain",
    "“It always seems impossible until it’s done.” – Nelson Mandela",
    "“Don’t watch the clock; do what it does. Keep going.” – Sam Levenson",
    "“Success is not final; failure is not fatal: It is the courage to continue that counts.”",
    "“Focus on being productive instead of busy.” – Tim Ferriss"
]


class DrawingWidget(Widget):
    def __init__(self, existing_lines=None, **kwargs):
        super().__init__(**kwargs)
        self.lines = existing_lines or []
        with self.canvas:
            Color(0.1, 0.1, 0.1, 1)
            for line_pts in self.lines:
                if len(line_pts) >= 4:
                    Line(points=line_pts, width=dp(3))

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.ud['line'] = [touch.x, touch.y]
            self.lines.append(touch.ud['line'])
            with self.canvas:
                Color(0.1, 0.1, 0.1, 1)
                touch.ud['instruction'] = Line(points=touch.ud['line'], width=dp(3))
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if 'line' in touch.ud:
            touch.ud['line'].extend([touch.x, touch.y])
            touch.ud['instruction'].points = touch.ud['line']
            return True
        return super().on_touch_move(touch)

    def clear_drawing(self):
        self.lines.clear()
        self.canvas.clear()


class NoteCard(BoxLayout):
    def __init__(self, note, app, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(6),
            padding=dp(12),
            **kwargs
        )
        self.note = note
        self.app = app
        self.height = dp(220)

        rgba = note.get("color", NOTE_COLORS[0][1])
        if not isinstance(rgba, (list, tuple)) or len(rgba) != 4:
            rgba = NOTE_COLORS[0][1]

        is_default_color = (list(rgba) == list(NOTE_COLORS[0][1]))
        if app.dark_mode and is_default_color:
            bg_rgba = (0.20, 0.22, 0.26, 1)
            title_color = (0.95, 0.95, 0.97, 1)
            content_color = (0.80, 0.82, 0.86, 1)
        else:
            bg_rgba = rgba
            title_color = (0.12, 0.13, 0.15, 1)
            content_color = (0.25, 0.26, 0.28, 1)

        with self.canvas.before:
            Color(*bg_rgba)
            self.bg = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(16)]
            )
        self.bind(pos=self.update_bg, size=self.update_bg)

        f_size = "18sp" if app.font_size_pref == "Large" else "16sp"
        c_size = "14sp" if app.font_size_pref == "Large" else "12sp"

        title = Label(
            text=("📌 " if note.get("pinned") else "") + note.get("title", "Untitled"),
            color=title_color, font_size=f_size, bold=True,
            halign="left", valign="middle", size_hint_y=None, height=dp(26)
        )
        title.bind(size=lambda obj, size: setattr(obj, "text_size", (size[0], None)))
        self.add_widget(title)

        tag = note.get("tag", "General")
        if tag:
            tag_lbl = Label(
                text=f"🏷️ {tag}",
                color=(0.15, 0.45, 0.75, 1) if not (app.dark_mode and is_default_color) else (0.5, 0.75, 1.0, 1),
                font_size="11sp", bold=True, halign="left", valign="middle",
                size_hint_y=None, height=dp(18)
            )
            tag_lbl.bind(size=lambda obj, size: setattr(obj, "text_size", (size[0], None)))
            self.add_widget(tag_lbl)

        note_type = note.get("type", "text")
        if note_type == "list":
            items = note.get("items", [])
            checked = sum(1 for item in items if item.get("checked", False))
            preview = "\n".join(
                ("☑ " if item.get("checked", False) else "☐ ") + item.get("text", "")
                for item in items[:2]
            )
            if not items:
                preview = "Empty checklist"
            preview += f"\n({checked}/{len(items)} completed)"
            content = Label(text=preview, color=content_color, font_size=c_size, halign="left", valign="top")
        elif note_type == "drawing":
            content = Label(text="🎨 [Drawing Note with Canvas]", color=content_color, font_size=c_size, halign="left", valign="top")
        elif note_type == "image":
            img_desc = note.get("image_text", "Image Note")
            content = Label(text=f"🖼️ {img_desc}", color=content_color, font_size=c_size, halign="left", valign="top")
        elif note_type == "audio":
            aud_desc = note.get("audio_text", "Voice Note")
            content = Label(text=f"🎙️ {aud_desc}", color=content_color, font_size=c_size, halign="left", valign="top")
        else:
            text_content = note.get("content", "")
            words_count = len(text_content.split())
            chars_count = len(text_content)
            content = Label(text=text_content + f"\n\n[Words: {words_count} | Chars: {chars_count}]", color=content_color, font_size=c_size, halign="left", valign="top")
        
        content.bind(size=lambda obj, size: setattr(obj, "text_size", (size[0], None)))
        self.add_widget(content)

        reminder_str = note.get("reminder", "")
        if reminder_str:
            rem_label = Label(
                text="🔔 " + reminder_str,
                color=(0.75, 0.25, 0.15, 1) if not (app.dark_mode and is_default_color) else (1.0, 0.65, 0.55, 1),
                font_size="10sp", bold=True, halign="left", valign="middle",
                size_hint_y=None, height=dp(18)
            )
            rem_label.bind(size=lambda obj, size: setattr(obj, "text_size", (size[0], None)))
            self.add_widget(rem_label)

        actions = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(4))
        if note.get("trashed", False):
            restore_btn = Button(text="Restore", font_size="11sp")
            restore_btn.bind(on_release=lambda *_: app.restore_note(note))
            del_forever_btn = Button(
                text="Delete", font_size="11sp",
                background_normal="", background_color=(0.85, 0.25, 0.25, 1), color=(1, 1, 1, 1)
            )
            del_forever_btn.bind(on_release=lambda *_: app.delete_forever(note))
            actions.add_widget(restore_btn)
            actions.add_widget(del_forever_btn)
        else:
            edit_btn = Button(text="Edit", font_size="11sp")
            if note_type == "list":
                edit_btn.bind(on_release=lambda *_: app.open_list_editor(note))
            elif note_type == "drawing":
                edit_btn.bind(on_release=lambda *_: app.open_drawing_editor(note))
            elif note_type == "image":
                edit_btn.bind(on_release=lambda *_: app.open_image_editor(note))
            elif note_type == "audio":
                edit_btn.bind(on_release=lambda *_: app.open_audio_editor(note))
            else:
                edit_btn.bind(on_release=lambda *_: app.open_editor(note))

            color_btn = Button(text="Color", font_size="11sp")
            color_btn.bind(on_release=lambda *_: app.open_color_picker(note))

            export_btn = Button(text="Export", font_size="11sp")
            export_btn.bind(on_release=lambda *_: app.export_note(note))

            arch_text = "Unarch" if note.get("archived", False) else "Arch"
            arch_btn = Button(text=arch_text, font_size="11sp")
            arch_btn.bind(on_release=lambda *_: app.toggle_archive(note))

            pin_btn = Button(text="📌" if note.get("pinned") else "Pin", font_size="11sp")
            pin_btn.bind(on_release=lambda *_: app.toggle_pin(note))

            delete_btn = Button(text="Trash", font_size="11sp")
            delete_btn.bind(on_release=lambda *_: app.delete_note(note))

            actions.add_widget(edit_btn)
            actions.add_widget(color_btn)
            actions.add_widget(export_btn)
            actions.add_widget(arch_btn)
            actions.add_widget(pin_btn)
            actions.add_widget(delete_btn)

        self.add_widget(actions)

    def update_bg(self, *_):
        self.bg.pos = self.pos
        self.bg.size = self.size


class MeviraKeep(App):
    def build(self):
        self.title = APP_NAME
        self.notes = []
        self.search_query = ""
        self.current_view = "notes"
        self.selected_tag = "All"
        self.dark_mode = False
        self.font_size_pref = "Normal"
        self.load_notes()

        self.root_layout = BoxLayout(orientation="vertical")
        self.show_splash_screen()
        return self.root_layout

    def show_splash_screen(self):
        self.root_layout.clear_widgets()
        splash_box = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(10))
        
        with splash_box.canvas.before:
            Color(0.94, 0.95, 0.97, 1)
            self.splash_bg = Rectangle(pos=splash_box.pos, size=Window.size)
        splash_box.bind(pos=self.update_splash_bg, size=self.update_splash_bg)

        logo_label = Label(text="💡", font_size="70sp", size_hint_y=None, height=dp(120))
        title_label = Label(text="Mevira Notes", font_size="32sp", bold=True, color=(0.12, 0.13, 0.16, 1), size_hint_y=None, height=dp(50))
        sub_label = Label(text="Your Personal Notes App", font_size="14sp", color=(0.4, 0.4, 0.4, 1), size_hint_y=None, height=dp(30))

        splash_box.add_widget(Widget())
        splash_box.add_widget(logo_label)
        splash_box.add_widget(title_label)
        splash_box.add_widget(sub_label)
        splash_box.add_widget(Widget())

        self.root_layout.add_widget(splash_box)
        Clock.schedule_once(self.load_main_interface, 2.0)

    def update_splash_bg(self, instance, *args):
        self.splash_bg.pos = instance.pos
        self.splash_bg.size = instance.size

    def load_main_interface(self, dt):
        self.root_layout.clear_widgets()
        
        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))
        header = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(8))

        menu_btn = Button(text="☰", size_hint_x=None, width=dp(48), font_size="20sp")
        menu_btn.bind(on_release=self.open_menu)

        self.search = TextInput(
            hint_text="Search your notes...", multiline=False, size_hint_y=None, height=dp(46),
            background_normal="", background_active="", background_color=(1, 1, 1, 1),
            foreground_color=(0.1, 0.1, 0.1, 1), padding=[dp(14), dp(12)]
        )
        self.search.bind(text=self.search_notes)

        self.theme_btn = Button(text="🌙", size_hint_x=None, width=dp(48), font_size="18sp")
        self.theme_btn.bind(on_release=lambda *_: self.toggle_dark_mode())

        header.add_widget(menu_btn)
        header.add_widget(self.search)
        header.add_widget(self.theme_btn)
        root.add_widget(header)

        self.heading = Label(
            text="MEVIRA KEEP — NOTES", font_size="20sp", bold=True,
            color=(0.12, 0.13, 0.16, 1), size_hint_y=None, height=dp(34)
        )
        root.add_widget(self.heading)

        self.scroll = ScrollView()
        self.grid = GridLayout(cols=1, spacing=dp(10), padding=dp(2), size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter("height"))
        self.scroll.add_widget(self.grid)
        root.add_widget(self.scroll)

        bottom = BoxLayout(size_hint_y=None, height=dp(65), spacing=dp(10))
        self.status = Label(text="Your notes are saved on this device", font_size="12sp", color=(0.25, 0.26, 0.3, 1))
        add_btn = Button(
            text="+", font_size="34sp", size_hint_x=None, width=dp(70),
            background_normal="", background_color=(0.80, 0.87, 1, 1), color=(0.05, 0.25, 0.65, 1)
        )
        add_btn.bind(on_release=self.open_add_menu)
        bottom.add_widget(self.status)
        bottom.add_widget(add_btn)
        root.add_widget(bottom)

        Clock.schedule_interval(self.check_reminders, 15)
        self.root_layout.add_widget(root)
        self.apply_theme()

    def load_notes(self):
        try:
            if DATA_FILE.exists():
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    self.notes = loaded.get("notes", [])
                    self.dark_mode = loaded.get("dark_mode", False)
                    self.font_size_pref = loaded.get("font_size_pref", "Normal")
                elif isinstance(loaded, list):
                    self.notes = loaded
        except Exception:
            self.notes = []

    def save_notes(self):
        try:
            data = {
                "notes": self.notes,
                "dark_mode": self.dark_mode,
                "font_size_pref": self.font_size_pref
            }
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.status.text = "Notes saved"
        except Exception as error:
            self.status.text = "Save error: " + str(error)

    def apply_theme(self):
        if self.dark_mode:
            Window.clearcolor = (0.10, 0.11, 0.13, 1)
            if hasattr(self, 'heading'):
                self.heading.color = (0.92, 0.94, 0.98, 1)
            if hasattr(self, 'status'):
                self.status.color = (0.70, 0.72, 0.78, 1)
            if hasattr(self, 'search'):
                self.search.background_color = (0.20, 0.22, 0.26, 1)
                self.search.foreground_color = (0.95, 0.95, 0.97, 1)
            if hasattr(self, 'theme_btn'):
                self.theme_btn.text = "☀️"
        else:
            Window.clearcolor = (0.94, 0.95, 0.97, 1)
            if hasattr(self, 'heading'):
                self.heading.color = (0.12, 0.13, 0.16, 1)
            if hasattr(self, 'status'):
                self.status.color = (0.25, 0.26, 0.30, 1)
            if hasattr(self, 'search'):
                self.search.background_color = (1, 1, 1, 1)
                self.search.foreground_color = (0.1, 0.1, 0.1, 1)
            if hasattr(self, 'theme_btn'):
                self.theme_btn.text = "🌙"
        self.refresh_notes()

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()
        self.save_notes()

    def switch_view(self, view_name, tag="All"):
        self.current_view = view_name
        self.selected_tag = tag
        if view_name == "notes":
            self.heading.text = f"MEVIRA KEEP — {tag}"
        else:
            titles = {"reminders": "🔔 REMINDERS", "archive": "📌 ARCHIVE", "trash": "🗑️ TRASH"}
            self.heading.text = titles.get(view_name, "MEVIRA KEEP")
        self.refresh_notes()

    def refresh_notes(self, query=None):
        if not hasattr(self, 'grid'):
            return
        if query is None:
            query = self.search_query
        self.grid.clear_widgets()
        filtered = []
        for note in self.notes:
            is_trashed = note.get("trashed", False)
            is_archived = note.get("archived", False)
            has_reminder = bool(note.get("reminder"))
            note_tag = note.get("tag", "General")

            if self.current_view == "trash":
                if not is_trashed: continue
            elif self.current_view == "archive":
                if is_trashed or not is_archived: continue
            elif self.current_view == "reminders":
                if is_trashed or not has_reminder: continue
            else:
                if is_trashed or is_archived: continue
                if self.selected_tag != "All" and note_tag != self.selected_tag:
                    continue

            searchable = note.get("title", "") + " " + note.get("content", "") + " " + note_tag
            if note.get("type") == "list":
                searchable += " " + " ".join(item.get("text", "") for item in note.get("items", []))
            if query.lower() in searchable.lower():
                filtered.append(note)

        filtered.sort(key=lambda note: note.get("pinned", False), reverse=True)
        for note in filtered:
            self.grid.add_widget(NoteCard(note, self))

    def search_notes(self, instance, value):
        self.search_query = value
        self.refresh_notes(value)

    def add_quick_quote(self):
        selected_quote = random.choice(QUOTES)
        self.notes.append({
            "id": str(datetime.now().timestamp()),
            "title": "💡 Inspiration Quote",
            "tag": "Motivation",
            "content": selected_quote,
            "type": "text",
            "pinned": True,
            "archived": False,
            "trashed": False,
            "reminder": "",
            "reminder_fired": False,
            "color": list(NOTE_COLORS[3][1]),
            "created": datetime.now().isoformat(timespec="minutes")
        })
        self.save_notes()
        self.refresh_notes()
        self.show_message("✨ Quick Quote Note Added Successfully!")

    def open_add_menu(self, *_):
        layout = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        popup = Popup(title="Create a note", content=layout, size_hint=(0.85, 0.65))
        options = [
            ("📝 Text Note", "text"),
            ("☑ Checklist", "list"),
            ("🎨 Drawing Note", "drawing"),
            ("🖼️ Image Note", "image"),
            ("🎙️ Audio Note", "audio"),
            ("🎲 Quick Quote Note", "quote")
        ]
        for label, kind in options:
            btn = Button(text=label, size_hint_y=None, height=dp(42))
            def choose(_button, selected_kind=kind):
                popup.dismiss()
                if selected_kind == "list":
                    self.open_list_editor()
                elif selected_kind == "text":
                    self.open_editor()
                elif selected_kind == "drawing":
                    self.open_drawing_editor()
                elif selected_kind == "image":
                    self.open_image_editor()
                elif selected_kind == "audio":
                    self.open_audio_editor()
                elif selected_kind == "quote":
                    self.add_quick_quote()
            btn.bind(on_release=choose)
            layout.add_widget(btn)
        popup.open()

    def open_editor(self, note=None):
        existing = note or {}
        layout = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))
        title_input = TextInput(hint_text="Title", text=existing.get("title", ""), multiline=False, size_hint_y=None, height=dp(44))
        tag_input = TextInput(hint_text="Tag / Category (e.g., Work, Personal)", text=existing.get("tag", "General"), multiline=False, size_hint_y=None, height=dp(40))
        content_input = TextInput(hint_text="Write your note here...", text=existing.get("content", ""), multiline=True)
        save_btn = Button(text="Save Note", size_hint_y=None, height=dp(46))
        
        layout.add_widget(title_input)
        layout.add_widget(tag_input)
        layout.add_widget(content_input)
        layout.add_widget(save_btn)
        popup = Popup(title="Edit note" if note else "New text note", content=layout, size_hint=(0.94, 0.85))

        def save_note(*_):
            title = title_input.text.strip() or "Untitled"
            tag = tag_input.text.strip() or "General"
            content = content_input.text.strip()
            if not content and not title_input.text.strip():
                self.show_message("Write something first.")
                return
            if note:
                note["title"] = title
                note["tag"] = tag
                note["content"] = content
                note["type"] = "text"
                note["updated"] = datetime.now().isoformat(timespec="minutes")
            else:
                self.notes.append({
                    "id": str(datetime.now().timestamp()), "title": title, "tag": tag,
                    "content": content, "type": "text", "pinned": False,
                    "archived": False, "trashed": False, "reminder": "", "reminder_fired": False,
                    "color": list(NOTE_COLORS[0][1]), "created": datetime.now().isoformat(timespec="minutes")
                })
            self.save_notes()
            self.refresh_notes()
            popup.dismiss()

        save_btn.bind(on_release=save_note)
        popup.open()

    def open_list_editor(self, note=None):
        existing = note or {}
        items = [dict(item) for item in existing.get("items", [])]
        if not items: items = [{"text": "", "checked": False}]

        layout = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        title_input = TextInput(hint_text="Checklist title", text=existing.get("title", ""), multiline=False, size_hint_y=None, height=dp(44))
        tag_input = TextInput(hint_text="Tag (e.g., Work, Personal)", text=existing.get("tag", "General"), multiline=False, size_hint_y=None, height=dp(40))
        
        rows = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None)
        rows.bind(minimum_height=rows.setter("height"))

        def rebuild_rows():
            rows.clear_widgets()
            for item in items:
                row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
                checkbox = CheckBox(active=bool(item.get("checked", False)), size_hint_x=None, width=dp(40))
                text_input = TextInput(hint_text="List item", text=item.get("text", ""), multiline=False)
                checkbox.bind(active=lambda _box, value, current=item: current.update({"checked": value}))
                text_input.bind(text=lambda _input, value, current=item: current.update({"text": value}))
                row.add_widget(checkbox)
                row.add_widget(text_input)
                rows.add_widget(row)

        rebuild_rows()
        item_scroll = ScrollView()
        item_scroll.add_widget(rows)
        add_item_btn = Button(text="+ Add item", size_hint_y=None, height=dp(40))
        save_btn = Button(text="Save Checklist", size_hint_y=None, height=dp(46))
        
        layout.add_widget(title_input)
        layout.add_widget(tag_input)
        layout.add_widget(item_scroll)
        layout.add_widget(add_item_btn)
        layout.add_widget(save_btn)
        popup = Popup(title="Edit checklist" if note else "New checklist", content=layout, size_hint=(0.95, 0.90))

        def add_item(*_):
            items.append({"text": "", "checked": False})
            rebuild_rows()

        def save_list(*_):
            cleaned_items = [{"text": i.get("text", "").strip(), "checked": bool(i.get("checked", False))} for i in items if i.get("text", "").strip()]
            title = title_input.text.strip() or "Checklist"
            tag = tag_input.text.strip() or "General"
            if not cleaned_items:
                self.show_message("Please add at least one item.")
                return
            if note:
                note["title"] = title
                note["tag"] = tag
                note["items"] = cleaned_items
                note["type"] = "list"
                note["updated"] = datetime.now().isoformat(timespec="minutes")
            else:
                self.notes.append({
                    "id": str(datetime.now().timestamp()), "title": title, "tag": tag, "content": "",
                    "items": cleaned_items, "type": "list", "pinned": False,
                    "archived": False, "trashed": False, "reminder": "", "reminder_fired": False,
                    "color": list(NOTE_COLORS[0][1]), "created": datetime.now().isoformat(timespec="minutes")
                })
            self.save_notes()
            self.refresh_notes()
            popup.dismiss()

        add_item_btn.bind(on_release=add_item)
        save_btn.bind(on_release=save_list)
        popup.open()

    def open_drawing_editor(self, note=None):
        existing = note or {}
        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        title_input = TextInput(hint_text="Drawing Title", text=existing.get("title", ""), multiline=False, size_hint_y=None, height=dp(40))
        tag_input = TextInput(hint_text="Tag (e.g., Work, Personal)", text=existing.get("tag", "General"), multiline=False, size_hint_y=None, height=dp(38))
        
        drawing_pad = DrawingWidget(existing_lines=existing.get("drawing_lines", []))
        
        btn_box = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        clear_btn = Button(text="Clear Canvas")
        save_btn = Button(text="Save Drawing")
        
        clear_btn.bind(on_release=lambda *_: drawing_pad.clear_drawing())
        btn_box.add_widget(clear_btn)
        btn_box.add_widget(save_btn)

        layout.add_widget(title_input)
        layout.add_widget(tag_input)
        layout.add_widget(drawing_pad)
        layout.add_widget(btn_box)

        popup = Popup(title="Drawing Note", content=layout, size_hint=(0.95, 0.90))

        def save_drawing_note(*_):
            title = title_input.text.strip() or "Drawing Note"
            tag = tag_input.text.strip() or "General"
            if note:
                note["title"] = title
                note["tag"] = tag
                note["drawing_lines"] = drawing_pad.lines
                note["type"] = "drawing"
                note["updated"] = datetime.now().isoformat(timespec="minutes")
            else:
                self.notes.append({
                    "id": str(datetime.now().timestamp()), "title": title, "tag": tag, "content": "",
                    "drawing_lines": drawing_pad.lines, "type": "drawing", "pinned": False,
                    "archived": False, "trashed": False, "reminder": "", "reminder_fired": False,
                    "color": list(NOTE_COLORS[0][1]), "created": datetime.now().isoformat(timespec="minutes")
                })
            self.save_notes()
            self.refresh_notes()
            popup.dismiss()

        save_btn.bind(on_release=save_drawing_note)
        popup.open()

    def open_image_editor(self, note=None):
        existing = note or {}
        layout = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))
        title_input = TextInput(hint_text="Image Note Title", text=existing.get("title", ""), multiline=False, size_hint_y=None, height=dp(44))
        tag_input = TextInput(hint_text="Tag (e.g., Work, Personal)", text=existing.get("tag", "General"), multiline=False, size_hint_y=None, height=dp(40))
        desc_input = TextInput(hint_text="Image description or file path...", text=existing.get("image_text", ""), multiline=True)
        save_btn = Button(text="Save Image Note", size_hint_y=None, height=dp(46))

        layout.add_widget(title_input)
        layout.add_widget(tag_input)
        layout.add_widget(desc_input)
        layout.add_widget(save_btn)

        popup = Popup(title="Image Note", content=layout, size_hint=(0.90, 0.70))

        def save_img_note(*_):
            title = title_input.text.strip() or "Image Note"
            tag = tag_input.text.strip() or "General"
            desc = desc_input.text.strip() or "Saved image note"
            if note:
                note["title"] = title
                note["tag"] = tag
                note["image_text"] = desc
                note["type"] = "image"
                note["updated"] = datetime.now().isoformat(timespec="minutes")
            else:
                self.notes.append({
                    "id": str(datetime.now().timestamp()), "title": title, "tag": tag, "content": "",
                    "image_text": desc, "type": "image", "pinned": False,
                    "archived": False, "trashed": False, "reminder": "", "reminder_fired": False,
                    "color": list(NOTE_COLORS[0][1]), "created": datetime.now().isoformat(timespec="minutes")
                })
            self.save_notes()
            self.refresh_notes()
            popup.dismiss()

        save_btn.bind(on_release=save_img_note)
        popup.open()

    def open_audio_editor(self, note=None):
        existing = note or {}
        layout = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))
        title_input = TextInput(hint_text="Audio Note Title", text=existing.get("title", ""), multiline=False, size_hint_y=None, height=dp(44))
        tag_input = TextInput(hint_text="Tag (e.g., Work, Personal)", text=existing.get("tag", "General"), multiline=False, size_hint_y=None, height=dp(40))
        desc_input = TextInput(hint_text="Voice note details or reminder...", text=existing.get("audio_text", "Voice memo recorded"), multiline=True)
        save_btn = Button(text="Save Audio Note", size_hint_y=None, height=dp(46))

        layout.add_widget(title_input)
        layout.add_widget(tag_input)
        layout.add_widget(desc_input)
        layout.add_widget(save_btn)

        popup = Popup(title="Audio Note", content=layout, size_hint=(0.90, 0.70))

        def save_audio_note(*_):
            title = title_input.text.strip() or "Audio Note"
            tag = tag_input.text.strip() or "General"
            desc = desc_input.text.strip() or "Voice memo recorded"
            if note:
                note["title"] = title
                note["tag"] = tag
                note["audio_text"] = desc
                note["type"] = "audio"
                note["updated"] = datetime.now().isoformat(timespec="minutes")
            else:
                self.notes.append({
                    "id": str(datetime.now().timestamp()), "title": title, "tag": tag, "content": "",
                    "audio_text": desc, "type": "audio", "pinned": False,
                    "archived": False, "trashed": False, "reminder": "", "reminder_fired": False,
                    "color": list(NOTE_COLORS[0][1]), "created": datetime.now().isoformat(timespec="minutes")
                })
            self.save_notes()
            self.refresh_notes()
            popup.dismiss()

        save_btn.bind(on_release=save_audio_note)
        popup.open()

    def export_note(self, note):
        try:
            filename = Path.home() / f"Note_{note.get('title', 'export').replace(' ', '_')}.txt"
            content_to_write = f"Title: {note.get('title')}\nTag: {note.get('tag')}\nCreated: {note.get('created')}\n\nContent:\n{note.get('content') or note.get('image_text') or note.get('audio_text') or 'Checklist/Drawing Note'}"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content_to_write)
            self.show_message(f"📤 Note exported successfully!\nSaved to:\n{filename}")
        except Exception as e:
            self.show_message("Export failed: " + str(e))

    def open_color_picker(self, note):
        layout = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        popup = Popup(title="Choose note color", content=layout, size_hint=(0.86, 0.75))
        for name, rgba in NOTE_COLORS:
            btn = Button(text=name, size_hint_y=None, height=dp(42), background_normal="", background_color=rgba, color=(0.12, 0.13, 0.15, 1))
            def choose_color(_button, selected_color=rgba):
                note["color"] = list(selected_color)
                self.save_notes()
                self.refresh_notes()
                popup.dismiss()
            btn.bind(on_release=choose_color)
            layout.add_widget(btn)
        popup.open()

    def toggle_pin(self, note):
        note["pinned"] = not note.get("pinned", False)
        self.save_notes()
        self.refresh_notes()

    def toggle_archive(self, note):
        note["archived"] = not note.get("archived", False)
        if note["archived"]: note["pinned"] = False
        self.save_notes()
        self.refresh_notes()

    def delete_note(self, note):
        note["trashed"] = True
        note["pinned"] = False
        self.save_notes()
        self.refresh_notes()

    def restore_note(self, note):
        note["trashed"] = False
        self.save_notes()
        self.refresh_notes()

    def delete_forever(self, note):
        if note in self.notes: self.notes.remove(note)
        self.save_notes()
        self.refresh_notes()

    def empty_trash(self):
        self.notes = [n for n in self.notes if not n.get("trashed", False)]
        self.save_notes()
        self.refresh_notes()

    def check_reminders(self, *_):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        triggered = False
        for note in self.notes:
            if note.get("trashed"): continue
            rem = note.get("reminder", "")
            if rem and not note.get("reminder_fired", False):
                if now_str >= rem:
                    note["reminder_fired"] = True
                    triggered = True
                    self.show_message(f"🔔 Reminder: {note.get('title', 'Untitled')}")
        if triggered:
            self.save_notes()
            self.refresh_notes()

    def open_calendar_view(self):
        layout = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        popup = Popup(title="🗓️ Notes Calendar View", content=layout, size_hint=(0.90, 0.80))

        scroll = ScrollView()
        grid = GridLayout(cols=1, spacing=dp(8), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))

        active_notes = [n for n in self.notes if not n.get("trashed")]
        active_notes.sort(key=lambda x: x.get("created", ""), reverse=True)

        if not active_notes:
            grid.add_widget(Label(text="No notes available.", size_hint_y=None, height=dp(40)))
        else:
            for note in active_notes:
                c_date = note.get("created", "Unknown Date")[:16].replace("T", " ")
                btn = Button(
                    text=f"📅 {c_date} | {note.get('title', 'Untitled')} (#{note.get('tag', 'General')})",
                    size_hint_y=None, height=dp(45), halign="left", valign="middle"
                )
                btn.bind(size=lambda obj, size: setattr(obj, "text_size", (size[0] - dp(20), None)))
                grid.add_widget(btn)

        scroll.add_widget(grid)
        layout.add_widget(scroll)
        popup.open()

    def open_menu(self, *_):
        layout = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        popup = Popup(title="Mevira Keep Menu", content=layout, size_hint=(0.85, 0.80))

        for label, view_key in [("📝 All Notes", "notes"), ("🔔 Reminders", "reminders"), ("📌 Archive", "archive"), ("🗑️ Trash", "trash"), ("🗓️ Calendar View", "calendar")]:
            btn = Button(text=label, size_hint_y=None, height=dp(40))
            if view_key == "calendar":
                btn.bind(on_release=lambda *_: (popup.dismiss(), self.open_calendar_view()))
            else:
                btn.bind(on_release=lambda _, vk=view_key: (popup.dismiss(), self.switch_view(vk, "All")))
            layout.add_widget(btn)

        unique_tags = sorted(list(set(n.get("tag", "General") for n in self.notes if not n.get("trashed"))))
        if unique_tags:
            tag_header = Button(text="--- Tags ---", size_hint_y=None, height=dp(25), disabled=True)
            layout.add_widget(tag_header)
            for t in unique_tags:
                t_btn = Button(text=f"🏷️ #{t}", size_hint_y=None, height=dp(38))
                t_btn.bind(on_release=lambda _, tag_name=t: (popup.dismiss(), self.switch_view("notes", tag_name)))
                layout.add_widget(t_btn)

        settings_btn = Button(text="⚙️ Statistics & Settings", size_hint_y=None, height=dp(40))
        settings_btn.bind(on_release=lambda *_: (popup.dismiss(), self.open_settings()))
        layout.add_widget(settings_btn)
        popup.open()

    def open_settings(self):
        layout = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))
        popup = Popup(title="App Statistics & Settings", content=layout, size_hint=(0.88, 0.70))

        total_notes = len([n for n in self.notes if not n.get("trashed")])
        trashed_notes = len([n for n in self.notes if n.get("trashed")])
        archived_notes = len([n for n in self.notes if n.get("archived") and not n.get("trashed")])

        stats_text = f"📊 Total Active Notes: {total_notes}\n📌 Archived Notes: {archived_notes}\n🗑️ Trash Notes: {trashed_notes}"
        stats_lbl = Label(text=stats_text, font_size="14sp", size_hint_y=None, height=dp(60), halign="left", valign="middle")
        stats_lbl.bind(size=lambda obj, size: setattr(obj, "text_size", (size[0], None)))

        font_label = f"Font Size: {self.font_size_pref}"
        font_btn = Button(text=font_label, size_hint_y=None, height=dp(44))
        def toggle_font(*_):
            self.font_size_pref = "Large" if self.font_size_pref == "Normal" else "Normal"
            font_btn.text = f"Font Size: {self.font_size_pref}"
            self.save_notes()
            self.refresh_notes()
        font_btn.bind(on_release=toggle_font)

        theme_label = "Switch to Light Mode ☀️" if self.dark_mode else "Switch to Dark Mode 🌙"
        theme_btn = Button(text=theme_label, size_hint_y=None, height=dp(44))
        theme_btn.bind(on_release=lambda *_: (self.toggle_dark_mode(), popup.dismiss()))

        empty_btn = Button(text="🗑️ Empty Trash Now", size_hint_y=None, height=dp(44), background_normal="", background_color=(0.85, 0.25, 0.25, 1), color=(1,1,1,1))
        empty_btn.bind(on_release=lambda *_: (self.empty_trash(), popup.dismiss()))

        layout.add_widget(stats_lbl)
        layout.add_widget(font_btn)
        layout.add_widget(theme_btn)
        layout.add_widget(empty_btn)
        popup.open()

    def show_message(self, message):
        popup = Popup(title="Mevira Keep", content=Label(text=message), size_hint=(0.85, 0.35))
        popup.open()


if __name__ == "__main__":
    MeviraKeep().run()
