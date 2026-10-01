import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import font as tkfont

try:
    from spellchecker import SpellChecker
except ImportError:
    SpellChecker = None


class TextEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Text Editor")
        self.root.geometry("900x650")

        self.spellchecker = SpellChecker() if SpellChecker else None
        self.spellcheck_job = None
        self.current_file = None

        self._build_menu()
        self._build_toolbar()
        self._build_editor()

        if not self.spellchecker:
            self.root.after(
                500,
                lambda: self.status.config(
                    text="Spell-check unavailable. Install with: pip install pyspellchecker"
                ),
            )

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="New", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open…", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As…", command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.destroy)
        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menubar)

        self.root.bind("<Control-n>", lambda event: self.new_file())
        self.root.bind("<Control-o>", lambda event: self.open_file())
        self.root.bind("<Control-s>", lambda event: self.save_file())

    def _build_toolbar(self):
        toolbar = tk.Frame(self.root, padx=6, pady=6)
        toolbar.pack(fill="x")

        tk.Label(toolbar, text="Find:").pack(side="left")
        self.search_entry = tk.Entry(toolbar, width=28)
        self.search_entry.pack(side="left", padx=(4, 6))
        self.search_entry.bind("<KeyRelease>", self.search_text)
        self.search_entry.bind("<Return>", self.find_next)

        tk.Button(toolbar, text="Next", command=self.find_next).pack(side="left")
        self.italic_button = tk.Button(
            toolbar, text="Italic", font=("TkDefaultFont", 9, "italic"),
            command=self.toggle_italic
        )
        self.italic_button.pack(side="left", padx=(10, 0))

        self.status = tk.Label(toolbar, text="", anchor="w")
        self.status.pack(side="left", padx=12)

    def _build_editor(self):
        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True)

        self.text = tk.Text(
            frame, wrap="word", undo=True, font=("Arial", 12),
            padx=12, pady=10
        )
        scrollbar = tk.Scrollbar(frame, command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)

        italic_font = tkfont.Font(self.text, self.text.cget("font"))
        italic_font.configure(slant="italic")
        self.text.tag_configure("italic", font=italic_font)
        self.text.tag_configure("search_match", background="#ffe680")
        self.text.tag_configure("misspelled", underline=True, foreground="#c00000")

        self.text.bind("<<Modified>>", self.on_text_modified)
        self.text.bind("<Button-3>", self.spelling_menu)

    def on_text_modified(self, _event=None):
        if self.text.edit_modified():
            self.text.edit_modified(False)
            self.schedule_spellcheck()

    def schedule_spellcheck(self):
        if not self.spellchecker:
            return
        if self.spellcheck_job:
            self.root.after_cancel(self.spellcheck_job)
        self.spellcheck_job = self.root.after(400, self.check_spelling)

    def check_spelling(self):
        self.spellcheck_job = None
        self.text.tag_remove("misspelled", "1.0", "end")

        if not self.spellchecker:
            return

        content = self.text.get("1.0", "end-1c")
        start = "1.0"

        for word in content.split():
            # Find each word in the widget so its position can be tagged.
            index = self.text.search(word, start, stopindex="end")
            if not index:
                continue

            end_index = f"{index}+{len(word)}c"
            cleaned = word.strip(".,!?;:()[]{}\"'")
            if cleaned and cleaned.isalpha() and cleaned.lower() not in self.spellchecker:
                self.text.tag_add("misspelled", index, end_index)

            start = end_index

    def toggle_italic(self):
        try:
            start = self.text.index("sel.first")
            end = self.text.index("sel.last")
        except tk.TclError:
            self.status.config(text="Select some text to italicize.")
            return

        # Toggle off only when the entire selection is already italic.
        if "italic" in self.text.tag_names(start):
            self.text.tag_remove("italic", start, end)
        else:
            self.text.tag_add("italic", start, end)

    def search_text(self, _event=None):
        self.text.tag_remove("search_match", "1.0", "end")
        query = self.search_entry.get()
        if not query:
            return

        start = "1.0"
        count = tk.IntVar()
        while True:
            index = self.text.search(query, start, stopindex="end", nocase=True, count=count)
            if not index:
                break
            end_index = f"{index}+{count.get()}c"
            self.text.tag_add("search_match", index, end_index)
            start = end_index

    def find_next(self, _event=None):
        query = self.search_entry.get()
        if not query:
            return

        start = self.text.index("insert")
        index = self.text.search(query, start, stopindex="end", nocase=True)
        if not index:
            index = self.text.search(query, "1.0", stopindex="end", nocase=True)

        if index:
            end_index = f"{index}+{len(query)}c"
            self.text.mark_set("insert", end_index)
            self.text.tag_remove("sel", "1.0", "end")
            self.text.tag_add("sel", index, end_index)
            self.text.see(index)
        else:
            self.status.config(text="No matches found.")

    def spelling_menu(self, event):
        if not self.spellchecker:
            return

        index = self.text.index(f"@{event.x},{event.y}")
        ranges = self.text.tag_ranges("misspelled")
        for i in range(0, len(ranges), 2):
            start, end = ranges[i], ranges[i + 1]
            if self.text.compare(start, "<=", index) and self.text.compare(index, "<", end):
                word = self.text.get(start, end).strip(".,!?;:()[]{}\"'")
                suggestions = self.spellchecker.candidates(word.lower()) or set()
                menu = tk.Menu(self.root, tearoff=False)

                for suggestion in sorted(suggestions)[:5]:
                    menu.add_command(
                        label=suggestion,
                        command=lambda s=suggestion, a=start, b=end:
                            self.replace_word(a, b, s),
                    )

                if not suggestions:
                    menu.add_command(label="No suggestions", state="disabled")

                menu.tk_popup(event.x_root, event.y_root)
                return

    def replace_word(self, start, end, replacement):
        original = self.text.get(start, end)
        # Keep punctuation around the misspelled word.
        left = original[:len(original) - len(original.lstrip(".,!?;:()[]{}\"'"))]
        right = original[len(original.rstrip(".,!?;:()[]{}\"'")):]
        self.text.delete(start, end)
        self.text.insert(start, f"{left}{replacement}{right}")
        self.schedule_spellcheck()

    def markdown_text(self):
        """Convert the editor contents and italic tags to Markdown."""
        result = []
        index = "1.0"
        end = self.text.index("end-1c")

        while self.text.compare(index, "<", end):
            next_index = self.text.index(f"{index}+1c")
            char = self.text.get(index, next_index)
            is_italic = "italic" in self.text.tag_names(index)

            # Add Markdown delimiters at italic-state transitions.
            if not result or is_italic != self._previous_italic:
                result.append("*")
            result.append(char)
            self._previous_italic = is_italic
            index = next_index

        if result and self._previous_italic:
            result.append("*")

        return "".join(result)

    def get_markdown(self):
        # Walk character-by-character, wrapping contiguous italic runs.
        output = []
        index = "1.0"
        end = self.text.index("end-1c")
        italic_open = False

        while self.text.compare(index, "<", end):
            next_index = self.text.index(f"{index}+1c")
            italic = "italic" in self.text.tag_names(index)

            if italic and not italic_open:
                output.append("*")
                italic_open = True
            elif not italic and italic_open:
                output.append("*")
                italic_open = False

            output.append(self.text.get(index, next_index))
            index = next_index

        if italic_open:
            output.append("*")

        return "".join(output)

    def save_file(self):
        if self.current_file:
            self._write_file(self.current_file)
        else:
            self.save_as()

    def save_as(self):
        has_italics = bool(self.text.tag_ranges("italic"))
        extension = ".md" if has_italics else ".txt"
        filetypes = [("Markdown files", "*.md"), ("Text files", "*.txt"), ("All files", "*.*")]
        path = filedialog.asksaveasfilename(
            defaultextension=extension,
            filetypes=filetypes,
            initialfile=f"Untitled{extension}",
        )
        if path:
            self.current_file = path
            self._write_file(path)

    def _write_file(self, path):
        has_italics = bool(self.text.tag_ranges("italic"))
        content = self.get_markdown() if has_italics else self.text.get("1.0", "end-1c")

        try:
            with open(path, "w", encoding="utf-8") as file:
                file.write(content)
            self.current_file = path
            self.status.config(text=f"Saved: {path}")
        except OSError as error:
            messagebox.showerror("Save failed", str(error))

    def open_file(self):
        path = filedialog.askopenfilename(
            filetypes=[
                ("Text and Markdown files", "*.txt *.md"),
                ("All files", "*.*"),
            ]
        )
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()
        except OSError as error:
            messagebox.showerror("Open failed", str(error))
            return

        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)
        self.text.tag_remove("italic", "1.0", "end")
        self.current_file = path

        # Apply italics to simple Markdown spans: *italic text*.
        if path.lower().endswith(".md"):
            self._load_markdown_italics()
        self.status.config(text=f"Opened: {path}")

    def _load_markdown_italics(self):
        index = "1.0"
        while True:
            start = self.text.search("*", index, stopindex="end", regexp=False)
            if not start:
                break
            end = self.text.search("*", f"{start}+1c", stopindex="end", regexp=False)
            if not end:
                break

            self.text.tag_add("italic", f"{start}+1c", end)
            self.text.delete(end)
            self.text.delete(start)
            index = start

    def new_file(self):
        self.text.delete("1.0", "end")
        self.current_file = None
        self.status.config(text="New document")


if __name__ == "__main__":
    root = tk.Tk()
    app = TextEditor(root)
    root.mainloop()
