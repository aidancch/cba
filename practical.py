import json
import random
import csv
import os
from typing import List
import difflib
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import tkinter.font as tkfont

PROGRESS_FILE = "progress.csv"

PRACTICAL_DRINK_NAMES = [
    "Sex on the Beach",
    "Dirty Shirley",
    "Tom Collins",
    "Sea Breeze",
    "Oaxacan Old Fashioned",
    "Classic Manhattan",
    "Americano",
    "Daiquiri",
    "Honeysuckle",
    "French Martini",
    "Grasshopper",
    "Green Tea Shots",
    "Scooby Snacks",
    "Gimlet",
    "Piña Colada",
]
# PRACTICAL_DRINK_NAMES = [
#     "Dirty Shirley",
#     "Sea Breeze",
#     "Classic Manhattan",
#     "Honeysuckle"
# ]

# Map practical display names -> names as stored in recipes.json (if different)
NAME_ALIASES = {
    "Green Tea Shots": "Green Tea",
}


# ============================================================
# Data Model (very similar to original)
# ============================================================

class Cocktail:
    def __init__(self, name: str, category: str,
                 ingredients: List[str], served_in: str,
                 served: str, garnish: str):
        self.name = name
        self.category = category
        self.ingredients = ingredients
        self.served_in = served_in
        self.served = served
        self.garnish = garnish

    def full_recipe_parts(self) -> List[str]:
        """
        Return the canonical ordered list we expect the user to type:
        all ingredients (in order) + served_in + served + garnish.
        """
        return list(self.ingredients) + [self.served_in, self.served, self.garnish]

    def __repr__(self):
        return f"Cocktail(name='{self.name}', category='{self.category}')"


class RecipeBook:
    def __init__(self, json_file: str):
        self.recipes = self.load_recipes(json_file)

    def load_recipes(self, json_file: str) -> List[Cocktail]:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Cocktail(**r) for r in data]

    def get_by_name(self, name: str):
        return next((r for r in self.recipes
                     if r.name.lower() == name.lower()), None)


# ============================================================
# GUI Application – Practical Trainer
# ============================================================

class PracticalTrainerGUI:
    def __init__(self, root, book: RecipeBook):
        self.root = root
        self.book = book

        # Build the subset of practical cocktails
        self.cocktails = self._load_practical_cocktails()
        if not self.cocktails:
            messagebox.showerror(
                "Error",
                "No practical cocktails found. "
                "Check PRACTICAL_DRINK_NAMES and recipes.json."
            )
            raise SystemExit(1)

        # Per-drink progress (name -> {'correct': int, 'wrong': int})
        self.progress = {}
        self._load_progress_file()

        # ----------------------------------------------------
        # Window / fonts
        # ----------------------------------------------------
        self.root.title("🍸 Cocktail Practical Trainer")
        self.root.geometry("1000x750")

        BASE_FONT_SIZE = 16
        self.font_normal = tkfont.Font(family="Arial", size=BASE_FONT_SIZE)
        self.font_mono = tkfont.Font(family="Consolas", size=BASE_FONT_SIZE)
        self.font_title = tkfont.Font(
            family="Arial", size=BASE_FONT_SIZE + 2, weight="bold"
        )

        self.root.option_add("*Font", self.font_normal)
        self.root.option_add("*TCombobox*Listbox.Font", self.font_normal)

        # ----------------------------------------------------
        # State
        # ----------------------------------------------------
        self.current_cocktail = None

        # Build GUI
        self._create_widgets()
        self._create_text_tags()

        # Intro + first question
        self._print_intro()
        self._enable_answer_area()
        self._ask_new_question()

    # --------------------------------------------------------
    # Practical drink loading
    # --------------------------------------------------------

    def _load_practical_cocktails(self) -> List[Cocktail]:
        cocktails: List[Cocktail] = []
        missing = []

        for display_name in PRACTICAL_DRINK_NAMES:
            lookup_name = NAME_ALIASES.get(display_name, display_name)
            base = self.book.get_by_name(lookup_name)
            if not base:
                missing.append(display_name)
                continue

            # If alias used, clone with the display name
            if lookup_name != display_name:
                base = Cocktail(
                    name=display_name,
                    category=base.category,
                    ingredients=list(base.ingredients),
                    served_in=base.served_in,
                    served=base.served,
                    garnish=base.garnish,
                )

            cocktails.append(base)

        if missing:
            # Let the user know which ones are missing,
            # but still run with the ones we did find.
            msg = "These practical drinks were not found in recipes.json:\n"
            msg += "\n".join(f"- {m}" for m in missing)
            messagebox.showwarning("Missing recipes", msg)

        return cocktails

    # --------------------------------------------------------
    # Progress CSV handling
    # --------------------------------------------------------

    def _load_progress_file(self):
        # Default zeros for each cocktail
        self.progress = {
            c.name: {"correct": 0, "wrong": 0}
            for c in self.cocktails
        }

        if os.path.exists(PROGRESS_FILE):
            try:
                with open(PROGRESS_FILE, "r", encoding="utf-8", newline="") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        name = row.get("name")
                        if name in self.progress:
                            try:
                                self.progress[name]["correct"] = int(row.get("correct", 0))
                                self.progress[name]["wrong"] = int(row.get("wrong", 0))
                            except ValueError:
                                # Ignore malformed rows
                                pass
            except Exception as e:
                messagebox.showwarning("Progress file error", f"Could not read {PROGRESS_FILE}:\n{e}")

        # Ensure we write a clean progress file at startup
        self._save_progress_file()

    def _save_progress_file(self):
        try:
            with open(PROGRESS_FILE, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["name", "correct", "wrong", "percentage"])
                for c in self.cocktails:
                    stats = self.progress.get(c.name, {"correct": 0, "wrong": 0})
                    correct = stats["correct"]
                    wrong = stats["wrong"]
                    total = correct + wrong
                    pct = round((correct / total) * 100, 1) if total > 0 else 0.0
                    writer.writerow([c.name, correct, wrong, pct])
        except Exception as e:
            messagebox.showwarning("Progress file error", f"Could not write {PROGRESS_FILE}:\n{e}")

    def _update_progress(self, cocktail_name: str, is_correct: bool):
        stats = self.progress.setdefault(cocktail_name, {"correct": 0, "wrong": 0})
        if is_correct:
            stats["correct"] += 1
        else:
            stats["wrong"] += 1
        self._save_progress_file()

    # --------------------------------------------------------
    # Text area + printing helpers
    # --------------------------------------------------------

    def _create_text_tags(self):
        self.output.tag_config("green", foreground="#4CAF50")
        self.output.tag_config("red", foreground="#F44336")
        self.output.tag_config("yellow", foreground="#FFC107")
        self.output.tag_config("bold", font=self.font_title)

    def _print(self, text: str):
        """
        Smart print:
        - Lines beginning with '+' or '[+]' are green
        - Lines beginning with '-' or '[-]' are red
        """
        if text.startswith("[+]") or text.startswith("+"):
            self.output.insert("end", text + "\n", "green")
        elif text.startswith("[-]") or text.startswith("-"):
            self.output.insert("end", text + "\n", "red")
        else:
            self.output.insert("end", text + "\n")

        self.output.see("end")

    def _clear_output(self):
        self.output.delete("1.0", "end")

    def _enable_answer_area(self):
        self.user_input.configure(state="normal")
        self.submit_button.configure(state="normal")
        self.user_input.focus()

    # --------------------------------------------------------
    # UI layout
    # --------------------------------------------------------

    def _create_widgets(self):
        # Top instructions
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")

        ttk.Label(
            top, text="Cocktail Practical – Focus List", font=self.font_title
        ).pack(anchor="w")

        drinks_label = ", ".join(PRACTICAL_DRINK_NAMES)
        ttk.Label(top, text=drinks_label, wraplength=900).pack(anchor="w", pady=(4, 8))

        ttk.Label(
            top,
            text=(
                "Answer format (comma separated): ingredients..., served in, served, garnish\n"
                "Example:\n"
                "2 oz white rum, 1.5 oz coconut cream, 1.5 oz pineapple juice, "
                "0.5 oz lime juice, Rocks glass, on the rocks, cherry"
            ),
            wraplength=900,
        ).pack(anchor="w", pady=(0, 4))

        # Output area (diffs, feedback)
        self.output = scrolledtext.ScrolledText(
            self.root, wrap="word", font=self.font_mono, height=24
        )
        self.output.pack(fill="both", expand=True, padx=10, pady=10)

        # Bottom input area
        bottom = ttk.Frame(self.root, padding=10)
        bottom.pack(fill="x")

        self.user_input = ttk.Entry(bottom)
        self.user_input.pack(side="left", fill="x", expand=True)

        self.user_input.bind("<Return>", lambda e: self._submit_answer())

        self.submit_button = ttk.Button(bottom, text="Submit", command=self._submit_answer)
        self.submit_button.pack(side="right", padx=(10, 0))

    # --------------------------------------------------------
    # Intro + questions
    # --------------------------------------------------------

    def _print_intro(self):
        self._clear_output()
        self._print("Welcome to the 🍸 Cocktail Practical Trainer!\n")
        self._print("You'll be quizzed forever on these specific drinks.")
        self._print(
            "Each question will ask: “Make me a <cocktail name>.”\n"
            "You must type ALL ingredients in order, then the glass, how it's served, "
            "and the garnish – all separated by commas.\n"
        )
        self._print("If you’re wrong, you'll see a code-style diff and be asked to try again.")
        self._print("Drinks you miss more often will be asked more frequently.\n")

    def _compute_weight(self, cocktail_name: str) -> float:
        stats = self.progress.get(cocktail_name, {"correct": 0, "wrong": 0})
        correct = stats["correct"]
        wrong = stats["wrong"]
        # Base weight plus extra emphasis for wrong answers
        weight = 1.0 + 2.0 * wrong - 0.5 * correct
        if weight < 0.2:
            weight = 0.2
        return weight

    def _choose_weighted_cocktail(self) -> Cocktail:
        weights = [self._compute_weight(c.name) for c in self.cocktails]
        total = sum(weights)
        if total <= 0:
            return random.choice(self.cocktails)
        return random.choices(self.cocktails, weights=weights, k=1)[0]

    def _ask_new_question(self):
        self.current_cocktail = self._choose_weighted_cocktail()
        c = self.current_cocktail
        stats = self.progress.get(c.name, {"correct": 0, "wrong": 0})
        correct = stats["correct"]
        wrong = stats["wrong"]
        attempts = correct + wrong

        self._print("\n" + "=" * 70)
        self._print(f"Question: Make me a {c.name}.")

        if attempts > 0:
            pct = (correct / attempts) * 100 if attempts > 0 else 0
            self._print(
                f"(You've seen this {attempts} time(s): "
                f"{correct} correct, {wrong} wrong, {pct:.1f}% accuracy.)"
            )
        else:
            self._print("(New or rarely seen drink for you.)")

        self._print(
            "Format reminder: ingredients..., served in, served, garnish\n"
            "→ Your answer:"
        )
        self.user_input.delete(0, "end")
        self.user_input.focus()

    # --------------------------------------------------------
    # Submit handler
    # --------------------------------------------------------

    def _submit_answer(self):
        if not self.current_cocktail:
            return

        answer = self.user_input.get().strip()
        self.user_input.delete(0, "end")

        if not answer:
            return

        # Optional: small utility command
        if answer.lower() in {"stats", "progress"}:
            self._print_overall_progress()
            return

        self._check_answer(answer)

    def _check_answer(self, answer: str):
        c = self.current_cocktail

        user_parts = [p.strip() for p in answer.split(",") if p.strip()]
        user_norm = [p.lower() for p in user_parts]

        expected_parts = c.full_recipe_parts()
        expected_norm = [p.lower() for p in expected_parts]

        if user_norm == expected_norm:
            self._print("\n✅ Correct!")
            self._update_progress(c.name, is_correct=True)
            self._print("Full recipe:")
            self._print(", ".join(expected_parts))

            stats = self.progress.get(c.name, {"correct": 0, "wrong": 0})
            correct = stats["correct"]
            wrong = stats["wrong"]
            attempts = correct + wrong
            pct = (correct / attempts) * 100 if attempts > 0 else 0
            self._print(
                f"Updated stats for {c.name}: {correct} correct, {wrong} wrong "
                f"({pct:.1f}% accuracy).\n"
            )

            # Move on to another (weighted) drink
            self._ask_new_question()
            return

        # If we get here, the answer is wrong
        self._print("\n❌ Incorrect. Here's the diff between your answer and the correct recipe:\n")

        diff = difflib.unified_diff(
            user_parts,
            expected_parts,
            fromfile="your answer",
            tofile="correct",
            lineterm=""
        )

        for line in diff:
            # Colorize +/- lines
            if line.startswith("+"):
                self._print(f"[+] {line}")  # green
            elif line.startswith("-"):
                self._print(f"[-] {line}")  # red
            else:
                self._print(line)

        self._update_progress(c.name, is_correct=False)

        stats = self.progress.get(c.name, {"correct": 0, "wrong": 0})
        correct = stats["correct"]
        wrong = stats["wrong"]
        attempts = correct + wrong
        pct = (correct / attempts) * 100 if attempts > 0 else 0

        self._print(
            f"\nCurrent stats for {c.name}: {correct} correct, {wrong} wrong "
            f"({pct:.1f}% accuracy)."
        )
        self._print("Try again for the SAME drink – type the full recipe once more.\n")

    def _print_overall_progress(self):
        self._print("\n===== Overall Progress (from progress.csv) =====")
        for c in self.cocktails:
            stats = self.progress.get(c.name, {"correct": 0, "wrong": 0})
            correct = stats["correct"]
            wrong = stats["wrong"]
            attempts = correct + wrong
            pct = (correct / attempts) * 100 if attempts > 0 else 0
            self._print(
                f"{c.name}: {correct} correct, {wrong} wrong, {pct:.1f}% accuracy"
            )
        self._print("==============================================\n")


# ============================================================
# Run GUI
# ============================================================

if __name__ == "__main__":
    root = tk.Tk()
    try:
        book = RecipeBook("recipes.json")  # must be in the same folder
    except FileNotFoundError:
        messagebox.showerror("File not found", "recipes.json not found next to practical.py")
        raise SystemExit(1)

    app = PracticalTrainerGUI(root, book)
    root.mainloop()
