import tkinter as tk
from tkinter import messagebox, ttk
import openai
import os
import requests
from PIL import Image, ImageTk
from io import BytesIO
import pyttsx3
import pygame  # For playing background music

class AdventureGPT:
    def __init__(self, root):
        self.root = root
        self.root.title("AdventureGPT")
        self.root.geometry("1200x900")
        self.root.configure(bg='#2E2E2E')

        self.story = ""
        self.character_type = ""
        self.world_type = ""
        self.player_name = ""
        self.setup_gui()
        self.init_openai()
        self.init_tts()  # Initialize text-to-speech
        self.init_music()  # Initialize music playback

    def setup_gui(self):
        self.screen_title = tk.StringVar()
        self.screen_title.set('AdventureGPT')
        self.user_input_var = tk.StringVar()

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TLabel', background='#2E2E2E', foreground='#FFFFFF', font=('Arial', 14))
        style.configure('TEntry', font=('Arial', 12))
        style.configure('TButton', font=('Arial', 12))
        style.configure('TFrame', background='#2E2E2E')

        ttk.Label(self.root, textvariable=self.screen_title, font=("Arial", 24)).pack(pady=10)

        self.setup_frame = ttk.Frame(self.root)
        self.setup_frame.pack(pady=20)

        ttk.Label(self.setup_frame, text="Character Type:").grid(row=0, column=0, pady=5)
        self.character_combo = ttk.Combobox(self.setup_frame, values=["Warrior", "Mage", "Rogue"])
        self.character_combo.grid(row=0, column=1, pady=5)

        ttk.Label(self.setup_frame, text="World Type:").grid(row=1, column=0, pady=5)
        self.world_combo = ttk.Combobox(self.setup_frame, values=["Fantasy", "Sci-Fi", "Post-Apocalyptic"])
        self.world_combo.grid(row=1, column=1, pady=5)

        ttk.Label(self.setup_frame, text="Your Name:").grid(row=2, column=0, pady=5)
        self.name_entry = ttk.Entry(self.setup_frame)
        self.name_entry.grid(row=2, column=1, pady=5)

        ttk.Button(self.setup_frame, text="Start Adventure", command=self.start_adventure).grid(row=3, column=0, columnspan=2, pady=10)

        self.game_frame = ttk.Frame(self.root)
        self.text_display = tk.Text(self.game_frame, state=tk.DISABLED, font=("Arial", 12), wrap=tk.WORD, bg='#3E3E3E', fg='#FFFFFF', height=20)
        self.text_display.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        self.user_input = ttk.Entry(self.game_frame, textvariable=self.user_input_var, font=("Arial", 14), width=50)
        self.user_input.pack(padx=20, pady=10)

        self.button_frame = ttk.Frame(self.game_frame)
        self.button_frame.pack(pady=10)

        self.submit_btn = ttk.Button(self.button_frame, text="Submit", command=self.submit)
        self.submit_btn.grid(row=0, column=0, padx=5)
        self.save_btn = ttk.Button(self.button_frame, text="Save", state=tk.DISABLED, command=self.save)
        self.save_btn.grid(row=0, column=1, padx=5)
        self.generate_image_btn = ttk.Button(self.button_frame, text="Generate Image", command=self.generate_image)
        self.generate_image_btn.grid(row=0, column=2, padx=5)
        ttk.Button(self.button_frame, text="Exit", command=self.story_done).grid(row=0, column=3, padx=5)

        self.loading_label = ttk.Label(self.game_frame, text="")
        self.loading_label.pack(pady=5)

        self.hint_label = ttk.Label(self.game_frame, text="Tip: You can type your own option or click a button below", font=("Arial", 10))
        self.hint_label.pack(pady=5)

        self.image_label = ttk.Label(self.game_frame)
        self.image_label.pack(pady=10)

        self.option_buttons = []

        # Bind mouse click event to text display for TTS
        self.text_display.bind("<Button-1>", self.read_text)

    def init_openai(self):
        api_key_file = "APIKey.txt"
        if os.path.exists(api_key_file) and os.path.getsize(api_key_file) > 0:
            with open(api_key_file, "r") as f:
                api_key = f.readline().strip()
                openai.api_key = api_key
        else:
            messagebox.showerror("Error", "API KEY NEEDED. Please create 'APIKey.txt' with your OpenAI API key.")
            self.root.destroy()

    def init_tts(self):
        """Initialize the text-to-speech engine."""
        self.tts_engine = pyttsx3.init()

    def init_music(self):
        """Initialize music playback."""
        pygame.mixer.init()
        pygame.mixer.music.load("background_music.mp3")  # Load your background music file
        pygame.mixer.music.set_volume(0.1)  # Set volume level (0.0 to 1.0)
        pygame.mixer.music.play(-1)  # Loop the music

    def start_adventure(self):
        self.character_type = self.character_combo.get()
        self.world_type = self.world_combo.get()
        self.player_name = self.name_entry.get()

        if not all([self.character_type, self.world_type, self.player_name]):
            messagebox.showwarning("Missing Information", "Please fill in all fields before starting the adventure.")
            return

        self.setup_frame.pack_forget()
        self.game_frame.pack(expand=True, fill=tk.BOTH)

        self.prompt = f"""You are an AI storyteller creating an interactive adventure.
        The player's name is {self.player_name}, a {self.character_type} in a {self.world_type} world.
        Create an engaging and interactive story based on these elements.
        After each story segment, provide 3 numbered options for the player to choose from.
        Keep your responses concise, under 200 words.
        Only end the story if the player types 'End Story.'"""

        self.generate_response("Start the story")

    def update_display(self):
        self.text_display.config(state=tk.NORMAL)
        self.text_display.delete("1.0", tk.END)
        self.text_display.insert(tk.END, self.story)
        self.text_display.config(state=tk.DISABLED)
        self.text_display.see(tk.END)

    def submit(self):
        user_input = self.user_input_var.get()
        self.user_input_var.set("")
        if user_input:
            self.story += f"You: {user_input}\n"
            self.update_display()
            self.generate_response(user_input)

    def generate_response(self, user_input):
        self.loading_label.config(text="Generating story...")
        self.root.update()

        for btn in self.option_buttons:
            btn.destroy()
        self.option_buttons.clear()

        messages = [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": user_input}
        ]

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            reply = response.choices[0].message.content
            self.story += f"AdventureGPT: {reply}\n\n"
            self.update_display()
            self.save_btn.config(state=tk.NORMAL)

            # Extract options from the reply
            options = [line.strip() for line in reply.split('\n') if line.strip().startswith(('1.', '2.', '3.'))]
            for i, option in enumerate(options):
                btn = ttk.Button(self.button_frame, text=option, command=lambda o=option: self.choose_option(o))
                btn.grid(row=1, column=i, padx=5, pady=5)
                self.option_buttons.append(btn)

                # Add a play button for TTS on each option
                play_button = ttk.Button(self.button_frame, text="🔊", command=lambda text=option: self.play_tts(text))
                play_button.grid(row=1, column=i+len(options), padx=5)

            # Add TTS button for the AI's response
            tts_button = ttk.Button(self.button_frame, text="🔊", command=lambda text=reply: self.play_tts(text))
            tts_button.grid(row=0, column=len(options)+1, padx=5)

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
        finally:
            self.loading_label.config(text="")

    def choose_option(self, option):
        self.user_input_var.set(option)
        self.submit()

    def play_tts(self, text):
        """Play text-to-speech for the given text."""
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    def generate_image(self):
        self.loading_label.config(text="Generating image...")
        self.root.update()

        try:
            story_segment = self.story.split("AdventureGPT:")[-1].strip()
            response = openai.Image.create(
                prompt=f"A scene from a {self.world_type} story featuring a {self.character_type}: {story_segment[:900]}",
                n=1,
                size="512x512"
            )
            image_url = response['data'][0]['url']
            self.display_image(image_url)
        except Exception as e:
            messagebox.showerror("Error", f"Error generating image: {e}")
        finally:
            self.loading_label.config(text="")

    def display_image(self, url):
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        img = img.resize((512, 512), Image.LANCZOS)  # Use LANCZOS for resizing
        photo = ImageTk.PhotoImage(img)

        # Open the image in a new window
        self.image_window = tk.Toplevel(self.root)
        self.image_window.title("Generated Image")
        self.image_window.geometry("600x600")
        img_label = tk.Label(self.image_window, image=photo)
        img_label.image = photo  # Keep a reference to avoid garbage collection
        img_label.pack(padx=20, pady=20)

    def read_text(self, event):
        """Read the text at the clicked position."""
        try:
            index = self.text_display.index("@%d,%d" % (event.x, event.y))
            clicked_text = self.text_display.get(index, "%s lineend" % index)  # Get the line where the click occurred
            if clicked_text:
                self.tts_engine.say(clicked_text.strip())
                self.tts_engine.runAndWait()
        except tk.TclError:
            pass  # Ignore errors if the click is outside valid text

    def save(self):
        with open("savefile.txt", "w") as f:
            f.write(f"Character: {self.character_type}\nWorld: {self.world_type}\nName: {self.player_name}\n\n")
            f.write(self.story)
        messagebox.showinfo("Saved Game", "Game saved successfully!")

    def story_done(self):
        pygame.mixer.music.stop()  # Stop the music when exiting
        self.root.destroy()
        print("Thanks for playing! Your story is saved in 'savefile.txt'.")

if __name__ == "__main__":
    root = tk.Tk()
    app = AdventureGPT(root)
    root.mainloop()

