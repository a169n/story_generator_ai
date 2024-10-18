import tkinter as tk
from tkinter import messagebox, ttk
import requests  # For making HTTP requests
from PIL import Image, ImageTk
import pyttsx3
import pygame  # For playing background music
import os
import re
import io

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
        self.init_gemini()  # Initialize Gemini AI
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

    def init_gemini(self):
        """Initialize the Gemini AI API."""
        self.gemini_api_key = self.load_gemini_api_key()  # Load your Gemini API key

    def load_gemini_api_key(self):
        api_key_file = "GeminiAPIKey.txt"
        if os.path.exists(api_key_file) and os.path.getsize(api_key_file) > 0:
            with open(api_key_file, "r") as f:
                return f.readline().strip()
        else:
            messagebox.showerror("Error", "API KEY NEEDED. Please create 'GeminiAPIKey.txt' with your Gemini API key.")
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
        Your response should not include any instructions, code, or dialogue not directly related to the story. 
        Keep your responses concise, under 200 words.
        Only end the story if the player types 'End Story.'"""

        self.generate_response("Start the story")

    def update_display(self):
        self.text_display.config(state=tk.NORMAL)
        self.text_display.delete("1.0", tk.END)
        self.text_display.insert(tk.END, self.story)
        self.text_display.config(state=tk.DISABLED)
        self.text_display.see(tk.END)

    def sanitize_input(self, user_input):
        """Sanitize user input to prevent prompt injection."""
        return re.sub(r'[^\w\s,.?!]', '', user_input)  # Allow only alphanumeric and common punctuation

    def submit(self):
        user_input = self.user_input_var.get()
        sanitized_input = self.sanitize_input(user_input)
        self.user_input_var.set(sanitized_input)
        if sanitized_input:
            self.story += f"You: {sanitized_input}\n"
            self.update_display()
            self.generate_response(sanitized_input)

    def generate_response(self, user_input):
        self.loading_label.config(text="Generating story...")
        self.root.update()

        # Clear previous option buttons
        for btn in self.option_buttons:
            btn.destroy()
        self.option_buttons.clear()

        try:
            # Call the Gemini API for the story generation
            response = requests.post(
                f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={self.gemini_api_key}',
                headers={'Content-Type': 'application/json'},
                json={
                    'contents': [
                        {
                            'parts': [
                                {'text': user_input}
                            ]
                        }
                    ]
                }
            )
            response.raise_for_status()  # Raise an error for bad responses

            # Log the full response for debugging
            api_response = response.json()

            # Check if 'candidates' key exists and is not empty
            candidates = api_response.get('candidates')
            if candidates and len(candidates) > 0:
                content = candidates[0].get('content')  # Access content
                if content:
                    parts = content.get('parts')
                    if parts and len(parts) > 0:
                        reply = parts[0].get('text')
                        if reply:
                            # Add a prompt asking for the user's next move
                            self.story += f"AdventureGPT: {reply}\n\n"
                            self.story += "What would you like to do next?\n"  # Prompt for next action
                            self.update_display()
                            self.save_btn.config(state=tk.NORMAL)

                            # Provide three options as buttons
                            options = [
                                f"Option 1: {reply.split('.')[0]}...",  # Just a simple example
                                f"Option 2: {reply.split('.')[1]}..." if len(reply.split('.')) > 1 else "Try something else...",
                                f"Option 3: {reply.split('.')[2]}..." if len(reply.split('.')) > 2 else "Suggest your action..."
                            ]
                            for i, option in enumerate(options):
                                btn = ttk.Button(self.button_frame, text=option, command=lambda opt=option: self.submit_opt(opt))
                                btn.grid(row=0, column=4+i, padx=5)
                                self.option_buttons.append(btn)
            else:
                messagebox.showerror("Error", "No content received from Gemini API.")
        except requests.exceptions.HTTPError as e:
            messagebox.showerror("API Error", f"An error occurred while accessing the API: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
        finally:
            self.loading_label.config(text="")  # Reset loading label

    def submit_opt(self, option):
        """Submit the selected option and continue the story."""
        self.story += f"You chose: {option}\n"
        self.update_display()
        self.generate_response(option)

    def read_text(self, event):
        """Read selected text using TTS."""
        try:
            text_widget = event.widget
            cursor_index = text_widget.index("@%s,%s" % (event.x, event.y))
            word_start = text_widget.index(f"{cursor_index} wordstart")
            word_end = text_widget.index(f"{cursor_index} wordend")
            selected_text = text_widget.get(word_start, word_end).strip()
            if selected_text:
                self.tts_engine.say(selected_text)
                self.tts_engine.runAndWait()
        except Exception as e:
            print(f"Error reading text: {e}")

    def generate_image(self):
        """Generate an image based on the current story context."""
        self.loading_label.config(text="Generating image...")
        self.root.update()

        prompt = f"An illustration based on the story context: {self.story[-200:]}"  # Last 200 characters of the story for context

        try:
            # Replace with actual image generation service
            response = requests.post(
                'https://api.your-image-generation-service.com/generate',  # Placeholder URL
                json={"prompt": prompt}
            )
            response.raise_for_status()
            image_data = response.content

            # Create an image from the response data
            image = Image.open(io.BytesIO(image_data))
            self.show_image(image)
        except requests.exceptions.HTTPError as e:
            messagebox.showerror("Image Generation Error", f"An error occurred while generating the image: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred while processing the image: {str(e)}")
        finally:
            self.loading_label.config(text="")  # Reset loading label

    def show_image(self, image):
        """Display the generated image in a new window."""
        image_window = tk.Toplevel(self.root)
        image_window.title("Generated Image")
        image_window.geometry("800x600")
        
        # Convert image to PhotoImage
        photo = ImageTk.PhotoImage(image)

        # Create a label to display the image
        label = tk.Label(image_window, image=photo)
        label.image = photo  # Keep a reference to avoid garbage collection
        label.pack(expand=True, fill=tk.BOTH)

    def save(self):
        with open("adventure_story.txt", "w") as f:
            f.write(self.story)
        messagebox.showinfo("Save", "Story saved successfully!")

    def story_done(self):
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = AdventureGPT(root)
    root.mainloop()
