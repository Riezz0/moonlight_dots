#!/usr/bin/env python3

import gi
import os
import json
import subprocess
from pathlib import Path
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf

class PowerMenu(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="")
        self.set_default_size(400, 150)  # Wider window for horizontal layout
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_decorated(False)
        
        # Check for Hyprland
        self.is_hyprland = "HYPRLAND_INSTANCE_SIGNATURE" in os.environ
        
        # Load pywal colors
        self.wal_colors = self.load_wal_colors()
        
        # Setup UI
        self.setup_ui()
        self.apply_theme()
    
    def load_wal_colors(self):
        """Load colors from pywal's cache"""
        cache_dir = Path.home() / ".cache" / "wal"
        colors_file = cache_dir / "colors.json"
        
        if not colors_file.exists():
            return {
                'special': {
                    'background': '#282a36',
                    'foreground': '#f8f8f2',
                },
                'colors': {
                    'color0': '#21222c',
                    'color1': '#ff5555',
                    'color2': '#50fa7b',
                    'color3': '#f1fa8c',
                    'color4': '#bd93f9',
                    'color5': '#ff79c6',
                    'color6': '#8be9fd',
                    'color7': '#f8f8f2'
                }
            }
        
        with open(colors_file) as f:
            return json.load(f)
    
    def setup_ui(self):
        """Create horizontal button layout"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_box)
        
        # Button container (horizontal)
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        button_box.set_margin_top(20)
        button_box.set_margin_bottom(20)
        button_box.set_margin_start(20)
        button_box.set_margin_end(20)
        button_box.set_halign(Gtk.Align.CENTER)
        main_box.pack_start(button_box, True, True, 0)
        
        # Power buttons - only Shutdown, Reboot, Lock, Cancel
        buttons = [
            ("Lock", "system-lock-screen-symbolic", self.on_lock),
            ("Reboot", "system-reboot-symbolic", self.on_reboot),
            ("Shutdown", "system-shutdown-symbolic", self.on_shutdown),
            ("Cancel", "window-close-symbolic", self.on_cancel)
        ]
        
        for label, icon_name, handler in buttons:
            btn = self.create_button(label, icon_name)
            btn.connect("clicked", handler)
            button_box.pack_start(btn, False, False, 0)
    
    def create_button(self, label, icon_name):
        """Create styled button with icon and label"""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        try:
            icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
            box.pack_start(icon, False, False, 0)
        except:
            pass
        
        label_widget = Gtk.Label(label=label)
        box.pack_start(label_widget, False, False, 0)
        
        btn = Gtk.Button()
        btn.add(box)
        btn.set_relief(Gtk.ReliefStyle.NONE)
        btn.set_can_focus(False)
        btn.set_size_request(120, 60)  # Wider buttons for better click area
        return btn
    
    def apply_theme(self):
        """Apply pywal colors"""
        bg_color = self.wal_colors['special']['background']
        fg_color = self.wal_colors['special']['foreground']
        accent_color = self.wal_colors['colors']['color4']
        
        css = f"""
        * {{
            font-family: 'Sans';
            font-size: 14px;
        }}
        
        window {{
            background-color: {bg_color};
            border-radius: 0px;
            border: 2px solid {accent_color};
        }}
        
        label {{
            color: {fg_color};
        }}
        
        button {{
            background-color: shade({bg_color}, 1.1);
            color: {fg_color};
            border-radius: 0px;
            padding: 12px 24px;
            margin: 0;
            border: none;
            transition: all 0.2s ease;
        }}
        
        button:hover {{
            background-color: {accent_color};
            color: {bg_color};
        }}
        
        button:active {{
            background-color: shade({accent_color}, 0.9);
        }}
        """
        
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css.encode())
        
        screen = Gdk.Screen.get_default()
        style_context = self.get_style_context()
        style_context.add_provider_for_screen(
            screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def on_lock(self, widget):
        """Handle screen locking with hyprlock or fallback"""
        if self.is_hyprland:
            try:
                subprocess.run(["hyprlock"], check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                self.fallback_lock()
        else:
            self.fallback_lock()
        self.destroy()
    
    def fallback_lock(self):
        """Fallback lock methods"""
        lock_commands = [
            "loginctl lock-session",
            "dm-tool lock",
            "i3lock",
            "swaylock"
        ]
        for cmd in lock_commands:
            try:
                subprocess.run(cmd.split(), check=True)
                break
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
    
    def on_shutdown(self, widget):
        self.confirm_action("Shutdown", "Power off the system?", "systemctl poweroff")
    
    def on_reboot(self, widget):
        self.confirm_action("Reboot", "Restart the system?", "systemctl reboot")
    
    def on_cancel(self, widget):
        self.destroy()
    
    def confirm_action(self, action, message, command):
        """Styled confirmation dialog"""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=action
        )
        dialog.format_secondary_text(message)
        
        # Apply theme
        bg_color = self.wal_colors['special']['background']
        fg_color = self.wal_colors['special']['foreground']
        
        dialog.get_content_area().override_background_color(
            Gtk.StateFlags.NORMAL, 
            self.hex_to_rgba(bg_color))
        
        for label in dialog.get_message_area().get_children():
            if isinstance(label, Gtk.Label):
                label.override_color(
                    Gtk.StateFlags.NORMAL, 
                    self.hex_to_rgba(fg_color))
        
        response = dialog.run()
        if response == Gtk.ResponseType.YES:
            os.system(command)
            self.destroy()
        dialog.destroy()
    
    def hex_to_rgba(self, hex_color):
        """Convert hex color to Gdk.RGBA"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)/255
        g = int(hex_color[2:4], 16)/255
        b = int(hex_color[4:6], 16)/255
        return Gdk.RGBA(r, g, b, 1.0)

if __name__ == "__main__":
    win = PowerMenu()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
