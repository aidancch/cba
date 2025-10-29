import json
from typing import List

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


# === Example usage ===
if __name__ == "__main__":
    book = RecipeBook("recipes.json")

    # Print all cocktails with their ingredients
    book.show_all()

    # Example: Get a specific cocktail
    mojito = book.get_by_name("Mojito")
    if mojito:
        mojito.display()

    # Example: List all names
    print("All cocktail names:")
    print(book.list_names())

    # Example: Filter by category
    highballs = book.filter_by_category("Built Drinks: Highballs")
    print("\nHighball cocktails:")
    for drink in highballs:
        print("-", drink.name)
