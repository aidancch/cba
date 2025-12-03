import json
import random
from typing import List
import difflib

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

    def display(self):
        print(f"🍸 {self.name}")
        print(f"  Category: {self.category}")
        print(f"  Served in: {self.served_in} ({self.served})")
        print(f"  Garnish: {self.garnish}")
        print("  Ingredients:")
        for ing in self.ingredients:
            print(f"    - {ing}")
        print()


class RecipeBook:
    def __init__(self, json_file: str):
        self.recipes = self.load_recipes(json_file)

    def load_recipes(self, json_file: str) -> List[Cocktail]:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Cocktail(**r) for r in data]

    def list_names(self):
        """Return a list of all cocktail names."""
        return [r.name for r in self.recipes]

    def get_by_name(self, name: str):
        """Retrieve a cocktail by exact name."""
        return next((r for r in self.recipes if r.name.lower() == name.lower()), None)

    def filter_by_category(self, category: str):
        """Return all cocktails that match a given category."""
        return [r for r in self.recipes if r.category.lower() == category.lower()]

    def show_all(self):
        """Print all cocktails and their ingredients."""
        for r in self.recipes:
            r.display()

def quiz_on_category(book: RecipeBook, categories: list, num_questions: int = float('inf')):
    """Run an interactive quiz on cocktails from a given category."""
    drinks = []
    for category in categories:
        drinks += book.filter_by_category(category)
    if not drinks:
        print(f"No drinks found in category '{categories}'.")
        return

    print(f"\n🍹 Learning Mode: {categories}")
    print(f"There are {len(drinks)} drinks in this category.\n")

    # questions = random.sample(drinks, min(num_questions, len(drinks)))
    questions = drinks
    score = 0

    for i, drink in enumerate(questions, start=1):
        print(f"Question {i}: What are the main ingredients in the {drink.name}?")
        answer = input("Your answer (comma-separated): ").strip().lower()
        correct_ings = [ing.lower() for ing in drink.ingredients]

        # Check if user mentioned at least half correctly
        correct_count = sum(1 for a in answer.split(",") if a.strip() in correct_ings)
        if correct_count == len(correct_ings):
            print("✅ Correct! Here's the full list:")
        if correct_count >= len(correct_ings) / 2:
            print("😐 Correct enough! Here's the full list:")
            score += 1
        else:
            print("❌ Not quite. Here’s the right answer:")

        print(", ".join(drink.ingredients))
        print()

    print(f"🎯 Final Score: {score}/{len(questions)}")


def learn_on_category(book: RecipeBook, categories: list, num_questions: int = 5):
    """Run an interactive quiz on cocktails from a given category with retry + git diff feedback."""
    drinks = []
    for category in categories:
        drinks += book.filter_by_category(category)
    if not drinks:
        print(f"No drinks found in category '{categories}'.")
        return

    print(f"\n🍹 Learning Mode: {categories}")
    print(f"There are {len(drinks)} drinks in this category.\n")

    # questions = random.sample(drinks, min(num_questions, len(drinks)))
    questions = drinks
    score = 0

    for i, drink in enumerate(questions, start=1):
        print(f"Question {i}: What are the main ingredients in the {drink.name}?")
        correct_ings = [ing.strip().lower() for ing in drink.ingredients]

        while True:
            answer = input("Your answer (comma-separated): ").strip().lower()
            user_ings = [a.strip() for a in answer.split(",") if a.strip()]
            correct_count = sum(1 for a in user_ings if a in correct_ings)

            if correct_count == len(correct_ings):
                print("✅ Correct! Here's the full list:")
                score += 1
                break
            else:
                print("❌ Not quite. Here’s a diff to help you learn:")

                diff = difflib.unified_diff(
                    user_ings,
                    correct_ings,
                    fromfile="your answer",
                    tofile="correct ingredients",
                    lineterm="",
                )
                for line in diff:
                    if line.startswith("+"):
                        print(f"\033[92m{line}\033[0m")  # green for additions
                    elif line.startswith("-"):
                        print(f"\033[91m{line}\033[0m")  # red for missing
                    else:
                        print(line)

                print("\nTry again!\n")

        print(", ".join(drink.ingredients))
        print()

    print(f"🎯 Final Score: {score}/{len(questions)}")


def mcq_on_category(book: RecipeBook, categories: list, num_questions: int = 5):
    """Run an MCQ-based learning quiz on cocktails from a given category with retry + git diff feedback."""
    drinks = []
    for category in categories:
        drinks += book.filter_by_category(category)
    if not drinks:
        print(f"No drinks found in category '{categories}'.")
        return

    print(f"\n🍹 Learning Mode: {categories}")
    print(f"There are {len(drinks)} drinks in this category.\n")

    # questions = random.sample(drinks, min(num_questions, len(drinks)))
    questions = drinks
    score = 0

    for i, drink in enumerate(questions, start=1):
        print(f"\nQuestion {i}: Which of the following ingredient lists belongs to the '{drink.name}'?")

        # Generate 3 wrong answers from the same category
        wrong_choices = random.sample([d for d in drinks if d != drink], k=min(3, len(drinks) - 1))
        all_choices = [drink] + wrong_choices
        random.shuffle(all_choices)

        # Display answer options
        for idx, option in enumerate(all_choices, start=1):
            ingredients_preview = ", ".join(option.ingredients[:3])
            if len(option.ingredients) > 3:
                ingredients_preview += ", ..."
            print(f"  {idx}. {ingredients_preview}")

        correct_index = all_choices.index(drink) + 1

        # Retry until correct
        while True:
            try:
                answer = int(input("Your choice (1-4): "))
                if not (1 <= answer <= len(all_choices)):
                    raise ValueError
            except ValueError:
                print("⚠️ Please enter a valid option number.")
                continue

            chosen = all_choices[answer - 1]
            if chosen == drink:
                print("✅ Correct! Here's the full ingredient list:")
                print(", ".join(drink.ingredients))
                score += 1
                break
            else:
                print("❌ Not quite! Here’s how your choice differs from the correct one:\n")

                diff = difflib.unified_diff(
                    chosen.ingredients,
                    drink.ingredients,
                    fromfile=f"{chosen.name}",
                    tofile=f"{drink.name}",
                    lineterm="",
                )
                for line in diff:
                    if line.startswith("+"):
                        print(f"\033[92m{line}\033[0m")  # green = correct (missing)
                    elif line.startswith("-"):
                        print(f"\033[91m{line}\033[0m")  # red = wrong (extra)
                    else:
                        print(line)

                print("\nTry again!\n")

    print(f"\n🎯 Final Score: {score}/{len(questions)}")


# === Example usage ===
if __name__ == "__main__":
    book = RecipeBook("recipes.json")
    learn_on_category(book, ["Built Drinks: Negroni-Style Cocktails"])

# Built Drinks: Highballs

# Built Drinks: Old Fashioned-Style Cocktails

# Built Drinks: Manhattan-Style Cocktails

# Built Drinks: Negroni-Style Cocktails

# Shaken Drinks: Sour-Style Cocktails

# Shaken Drinks: Coffee, Cream, Egg Cocktails

# Shaken Drinks: Shooters

# Shaken or Stirred: Martini-Style Cocktails

# Shaken or Stirred: Sparkling Drinks