import json
import random
from typing import List
import difflib
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import tkinter.font as tkfont


# ============================================================
# Data Model (unchanged)
# ============================================================

class Cocktail:
    def __init__(self, name: str, category: str, ingredients: List[str], served_in: str, served: str, garnish: str):
        self.name = name
        self.category = category
        self.ingredients = ingredients
        self.served_in = served_in
        self.served = served
        self.garnish = garnish

    def __repr__(self):
        return f"Cocktail(name='{self.name}', category='{self.category}')"


class RecipeBook:
    def __init__(self, json_file: str):
        self.recipes = self.load_recipes(json_file)

    def load_recipes(self, json_file: str) -> List[Cocktail]:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Cocktail(**r) for r in data]

    def list_names(self):
        return [r.name for r in self.recipes]

    def get_by_name(self, name: str):
        return next((r for r in self.recipes if r.name.lower() == name.lower()), None)

    def filter_by_category(self, category: str):
        return [r for r in self.recipes if r.category.lower() == category.lower()]


# ============================================================
# GUI Application
# ============================================================

class CocktailTrainerGUI:
    def __init__(self, root, book: RecipeBook):
        self.root = root
        self.book = book

        self.root.title("🍸 Cocktail Trainer")
        self.root.geometry("1000x750")

        # ----------------------------------------------------
        # GLOBAL FONT CONFIGURATION
        # ----------------------------------------------------
        BASE_FONT_SIZE = 16
        self.font_normal = tkfont.Font(family="Arial", size=BASE_FONT_SIZE)
        self.font_mono = tkfont.Font(family="Consolas", size=BASE_FONT_SIZE)
        self.font_title = tkfont.Font(family="Arial", size=BASE_FONT_SIZE + 2, weight="bold")

        self.root.option_add("*Font", self.font_normal)
        self.root.option_add("*TCombobox*Listbox.Font", self.font_normal)

        # ----------------------------------------------------
        # State
        # ----------------------------------------------------
        self.current_drinks = []
        self.current_question_index = 0
        self.score = 0

        # Build GUI
        self.create_widgets()
        self.create_text_tags()

    # --------------------------------------------------------
    # Setup Text Color Tags
    # --------------------------------------------------------

    def create_text_tags(self):
        self.output.tag_config("green", foreground="#4CAF50")
        self.output.tag_config("red", foreground="#F44336")
        self.output.tag_config("yellow", foreground="#FFC107")
        self.output.tag_config("bold", font=self.font_title)

    # --------------------------------------------------------
    # Colored print()
    # --------------------------------------------------------

    def print(self, text):
        """
        Smart print:
        - Lines beginning with '+' are green
        - Lines beginning with '-' are red
        - Titles can be tagged manually using <color> markers if needed
        """

        # Detect diff colors
        if text.startswith("[+]") or text.startswith("+"):
            self.output.insert("end", text + "\n", "green")
        elif text.startswith("[-]") or text.startswith("-"):
            self.output.insert("end", text + "\n", "red")
        else:
            self.output.insert("end", text + "\n")

        self.output.see("end")

    # --------------------------------------------------------
    # Basic Helpers
    # --------------------------------------------------------

    def clear_output(self):
        self.output.delete("1.0", "end")

    def enable_answer_area(self):
        self.user_input.configure(state="normal")
        self.submit_button.configure(state="normal")
        self.user_input.focus()

    def disable_answer_area(self):
        self.user_input.configure(state="disabled")
        self.submit_button.configure(state="disabled")

    # --------------------------------------------------------
    # UI Layout
    # --------------------------------------------------------

    def create_widgets(self):
        # Top section
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill="x")

        ttk.Label(top_frame, text="Select Category:", font=self.font_title).pack(anchor="w")

        categories = sorted(set(r.category for r in self.book.recipes))

        self.category_var = tk.StringVar()
        self.category_dropdown = ttk.Combobox(
            top_frame,
            textvariable=self.category_var,
            values=categories,
            width=50
        )
        self.category_dropdown.pack(pady=5)

        # Mode Buttons
        mode_frame = ttk.Frame(self.root, padding=10)
        mode_frame.pack(fill="x")

        ttk.Button(mode_frame, text="Ingredient Quiz", command=self.start_quiz_mode).pack(side="left", padx=5)
        ttk.Button(mode_frame, text="Learning Mode", command=self.start_learning_mode).pack(side="left", padx=5)
        ttk.Button(mode_frame, text="MCQ Mode", command=self.start_mcq_mode).pack(side="left", padx=5)

        # Output Area
        self.output = scrolledtext.ScrolledText(
            self.root, wrap="word", font=self.font_mono, height=25
        )
        self.output.pack(fill="both", expand=True, padx=10, pady=10)

        # Bottom input area
        bottom = ttk.Frame(self.root)
        bottom.pack(fill="x")

        self.user_input = ttk.Entry(bottom)
        self.user_input.pack(side="left", fill="x", expand=True, padx=10)

        # ENTER → submit
        self.user_input.bind("<Return>", lambda e: self.submit_answer())

        self.submit_button = ttk.Button(bottom, text="Submit", command=self.submit_answer)
        self.submit_button.pack(side="right", padx=10)

        self.disable_answer_area()

    # --------------------------------------------------------
    # Mode: Ingredient Quiz
    # --------------------------------------------------------

    def start_quiz_mode(self):
        category = self.category_var.get()
        if not category:
            messagebox.showwarning("Select category", "Please select a category first.")
            return

        self.current_drinks = self.book.filter_by_category(category)
        if not self.current_drinks:
            messagebox.showerror("Error", "No cocktails in this category.")
            return
        
        random.shuffle(self.current_drinks)

        self.clear_output()
        self.print(f"🍹 Ingredient Quiz — {category}")
        self.print(f"{len(self.current_drinks)} drinks found.\n")

        self.current_question_index = 0
        self.score = 0
        self.enable_answer_area()
        self.ask_next_quiz_question()

    def ask_next_quiz_question(self):
        if self.current_question_index >= len(self.current_drinks):
            self.finish_quiz()
            return

        drink = self.current_drinks[self.current_question_index]
        self.print(f"\nQuestion {self.current_question_index + 1}: What are the main ingredients in {drink.name}?")

        self.user_input.delete(0, "end")
        self.expected_ingredients = [i.lower() for i in drink.ingredients]
        self.current_mode = "quiz"

    # --------------------------------------------------------
    # Mode: Learning Mode (diff)
    # --------------------------------------------------------

    def start_learning_mode(self):
        category = self.category_var.get()
        if not category:
            messagebox.showwarning("Select category", "Please select a category first.")
            return

        self.current_drinks = self.book.filter_by_category(category)
        if not self.current_drinks:
            messagebox.showerror("Error", "No cocktails in this category.")
            return

        # Reset and announce learning mode
        self.clear_output()
        self.print(f"🍹 Learning Mode — {category}\n")

        # Reset quiz state
        self.current_question_index = 0
        self.score = 0

        # Enable the answer input
        self.enable_answer_area()

        # Begin asking questions
        self.ask_next_learning_question()


    def ask_next_learning_question(self):
        if self.current_question_index >= len(self.current_drinks):
            self.finish_quiz()
            return

        drink = self.current_drinks[self.current_question_index]
        self.print(f"\nQuestion {self.current_question_index + 1}: Ingredients in {drink.name}?")

        self.user_input.delete(0, "end")
        self.expected_ingredients = [i.lower() for i in drink.ingredients]
        self.current_mode = "learn"

    # --------------------------------------------------------
    # Mode: MCQ
    # --------------------------------------------------------

    def start_mcq_mode(self):
        category = self.category_var.get()
        if not category:
            messagebox.showwarning("Select category", "Please select a category first.")
            return

        self.current_drinks = self.book.filter_by_category(category)
        if len(self.current_drinks) < 2:
            messagebox.showerror("Error", "Need at least 2 cocktails for MCQ.")
            return

        self.clear_output()
        self.print(f"🍹 MCQ Mode — {category}\n")

        self.current_question_index = 0
        self.score = 0
        self.ask_next_mcq_question()

    def ask_next_mcq_question(self):
        if self.current_question_index >= len(self.current_drinks):
            self.finish_quiz()
            return

        drink = self.current_drinks[self.current_question_index]
        self.clear_output()

        self.print(f"Question {self.current_question_index + 1}: Which ingredients belong to '{drink.name}'?\n")

        wrong = random.sample(
            [d for d in self.current_drinks if d != drink],
            k=min(3, len(self.current_drinks) - 1)
        )

        self.mcq_choices = [drink] + wrong
        random.shuffle(self.mcq_choices)

        for i, opt in enumerate(self.mcq_choices, start=1):
            preview = ", ".join(opt.ingredients)
            # if len(opt.ingredients) > 3:
            #     preview += ", ..."
            self.print(f"{i}. {preview}")

        self.current_mode = "mcq"
        self.enable_answer_area()
        self.user_input.delete(0, "end")

    # --------------------------------------------------------
    # Submit Handler
    # --------------------------------------------------------

    def submit_answer(self):
        answer = self.user_input.get().strip().lower()

        self.user_input.delete(0, "end")

        if self.current_mode == "quiz":
            self.handle_quiz_answer(answer)

        elif self.current_mode == "learn":
            self.handle_learning_answer(answer)

        elif self.current_mode == "mcq":
            self.handle_mcq_answer(answer)

    # --------------------- QUIZ ------------------------------

    def handle_quiz_answer(self, answer):
        drink = self.current_drinks[self.current_question_index]
        user_ings = [x.strip() for x in answer.split(",") if x.strip()]

        self.print("You entered")
        self.print(", ".join(user_ings))

        correct = sum(1 for x in user_ings if x in self.expected_ingredients)

        if correct == len(self.expected_ingredients):
            self.print("✅ Correct!")
            self.score += 1
        elif correct >= len(self.expected_ingredients) / 2:
            self.print("😐 Correct enough!")
            self.score += 1
        else:
            self.print("❌ Incorrect.")

        self.print("Correct ingredients:")
        self.print(", ".join(drink.ingredients))

        self.current_question_index += 1
        self.ask_next_quiz_question()

    # ------------------- LEARNING MODE -----------------------

    def handle_learning_answer(self, answer):
        drink = self.current_drinks[self.current_question_index]
        user_ings = [x.strip() for x in answer.split(",") if x.strip()]
        correct_count = sum(1 for x in user_ings if x in self.expected_ingredients)

        if correct_count == len(self.expected_ingredients):
            self.print("✅ Correct!\n")
            self.score += 1
            self.print(", ".join(drink.ingredients))
            self.current_question_index += 1
            self.ask_next_learning_question()
            return

        # Colored diff
        self.print("❌ Not correct. Here's the diff:\n")
        diff = difflib.unified_diff(
            user_ings, self.expected_ingredients,
            fromfile="your answer",
            tofile="correct",
            lineterm=""
        )

        for line in diff:
            if line.startswith("+"):
                self.print(f"[+] {line}")  # green
            elif line.startswith("-"):
                self.print(f"[-] {line}")  # red
            else:
                self.print(line)

        self.print("\nTry again.")

    # ------------------------ MCQ -----------------------------

    def handle_mcq_answer(self, answer):
        drink = self.current_drinks[self.current_question_index]

        try:
            n = int(answer)
        except:
            self.print("Enter a number from the list.")
            return

        if not (1 <= n <= len(self.mcq_choices)):
            self.print("Invalid option.")
            return

        chosen = self.mcq_choices[n - 1]

        if chosen == drink:
            self.print("\n✅ Correct!")
            self.print(", ".join(drink.ingredients))
            self.score += 1
            self.current_question_index += 1
            self.ask_next_mcq_question()
            return

        self.print("❌ Wrong. Diff:\n")

        diff = difflib.unified_diff(
            chosen.ingredients,
            drink.ingredients,
            fromfile=chosen.name,
            tofile=drink.name,
            lineterm=""
        )

        for line in diff:
            if line.startswith("+"):
                self.print(f"[+] {line}")  # green
            elif line.startswith("-"):
                self.print(f"[-] {line}")  # red
            else:
                self.print(line)

        self.print("\nTry again.")

    # --------------------------------------------------------
    # Finish
    # --------------------------------------------------------

    def finish_quiz(self):
        self.disable_answer_area()
        self.print(f"\n🎯 Final Score: {self.score}/{len(self.current_drinks)}")
        messagebox.showinfo("Quiz Finished", f"Final Score: {self.score}/{len(self.current_drinks)}")


# ============================================================
# Run GUI
# ============================================================

if __name__ == "__main__":
    root = tk.Tk()
    book = RecipeBook("recipes.json")
    app = CocktailTrainerGUI(root, book)
    root.mainloop()
