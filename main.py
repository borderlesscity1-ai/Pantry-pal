import os
import traceback
from google import genai
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock

GEMINI_API_KEY = "AQ.Ab8RN6Jyaw8h5g-FpDzVjHQ4bmg3vHOfJ9hbdsV-nOlO2J4zSg"

class PantryApp(App):
    def build(self):
        self.title = "Pantry Pal Pro"
        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        # Instruction header
        self.label = Label(
            text="Pantry Pal Pro Loaded!\nEnter your photo name and preferences below:",
            font_size=13,
            size_hint_y=None,
            height=40,
            halign='center',
            valign='middle'
        )
        self.label.bind(size=self.label.setter('text_size'))
        main_layout.add_widget(self.label)
        
        # Input container layout
        inputs_layout = BoxLayout(orientation='vertical', spacing=6, size_hint_y=None, height=135)
        
        # 1. Filename Input
        inputs_layout.add_widget(Label(text="Photo Filename:", font_size=11, size_hint_y=None, height=18))
        self.file_input = TextInput(text="IMG_20261103_122430.jpg", size_hint_y=None, height=35, multiline=False, font_size=13)
        inputs_layout.add_widget(self.file_input)
        
        # 2 & 4. Dietary Preference & Servings row
        row_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=55)
        
        diet_box = BoxLayout(orientation='vertical', size_hint_x=0.65)
        diet_box.add_widget(Label(text="Dietary Goal:", font_size=11, size_hint_y=None, height=18))
        self.diet_input = TextInput(text="High-Protein", font_size=12, size_hint_y=None, height=32, multiline=False)
        diet_box.add_widget(self.diet_input)
        row_layout.add_widget(diet_box)
        
        serv_box = BoxLayout(orientation='vertical', size_hint_x=0.35)
        serv_box.add_widget(Label(text="Servings:", font_size=11, size_hint_y=None, height=18))
        self.serv_input = TextInput(text="2", font_size=12, size_hint_y=None, height=32, multiline=False)
        serv_box.add_widget(self.serv_input)
        
        inputs_layout.add_widget(row_layout)
        main_layout.add_widget(inputs_layout)
        
        # Action Buttons Row (Scan + Save)
        btn_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=45)
        
        self.scan_btn = Button(
            text="Scan Photo",
            background_color=(0.1, 0.6, 0.9, 1),
            font_size=14
        )
        self.scan_btn.bind(on_press=self.analyze_image_file)
        btn_layout.add_widget(self.scan_btn)
        
        self.save_btn = Button(
            text="Save Recipe",
            background_color=(0.2, 0.7, 0.3, 1),
            font_size=14
        )
        self.save_btn.bind(on_press=self.save_recipe)
        btn_layout.add_widget(self.save_btn)
        
        main_layout.add_widget(btn_layout)
        
        # 1. Scrollable Output View
        self.output_label = Label(
            text="Your AI-generated recipe will appear here...\nScroll down anytime to read more!",
            font_size=13,
            halign='left',
            valign='top',
            size_hint_y=None
        )
        self.output_label.bind(width=lambda *x: setattr(self.output_label, 'text_size', (self.output_label.width, None)))
        self.output_label.bind(texture_size=lambda *x: setattr(self.output_label, 'height', self.output_label.texture_size[1]))
        
        self.scroll_view = ScrollView(size_hint=(1, 1))
        self.scroll_view.add_widget(self.output_label)
        main_layout.add_widget(self.scroll_view)
        
        self.last_recipe_text = ""
        return main_layout

    def analyze_image_file(self, instance):
        filename = self.file_input.text.strip()
        diet = self.diet_input.text.strip()
        servings = self.serv_input.text.strip()
        
        possible_paths = [
            filename,
            f"/sdcard/DCIM/Camera/{filename}",
            f"/sdcard/Pictures/{filename}",
            f"/sdcard/{filename}"
        ]
        
        target_path = None
        for path in possible_paths:
            if os.path.exists(path):
                target_path = path
                break
                
        if not target_path:
            self.output_label.text = f"❌ Error: Could not find '{filename}' in phone storage. Snap a photo with your camera app first!"
            return

        self.output_label.text = f"🔍 Analyzing photo for a '{diet}' meal ({servings} servings)..."
        self.scan_btn.disabled = True
        Clock.schedule_once(lambda dt: self.run_gemini_vision(target_path, diet, servings), 0.5)

    def run_gemini_vision(self, filepath, diet, servings):
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            sample_file = client.files.upload(file=filepath)
            
            prompt = f"Look at these ingredients in the photo and create 1 quick, easy recipe tailored for a '{diet}' dietary goal, scaled precisely for {servings} servings. Include prep time, cook time, ingredients with exact quantities, step-by-step instructions, and complete macros per serving."
            
            response = client.models.generate_content(
                model='gemini-3.5-flash',
                contents=[sample_file, prompt]
            )
            self.last_recipe_text = response.text
            self.output_label.text = response.text
        except Exception as e:
            self.output_label.text = f"❌ AI Error:\n{str(e)}"
        finally:
            self.scan_btn.disabled = False

    def save_recipe(self, instance):
        if not self.last_recipe_text:
            self.output_label.text = "⚠️ No recipe generated yet! Scan a photo first before saving."
            return
        try:
            save_path = "/sdcard/saved_recipes.txt"
            with open(save_path, "a", encoding="utf-8") as f:
                f.write("\n\n============================\n")
                f.write("PANTRY PAL PRO RECIPE SAVE\n")
                f.write("============================\n")
                f.write(self.last_recipe_text)
            self.output_label.text = f"✅ Success! Recipe saved locally to:\n{save_path}\n\n" + self.last_recipe_text
        except Exception as e:
            self.output_label.text = f"❌ Save Error:\n{str(e)}"

if __name__ == '__main__':
    PantryApp().run()
