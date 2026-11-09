-- 
-- depends: 
PRAGMA foreign_keys = ON;

CREATE TABLE customers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (first_name, last_name)
);

-- 1. Таблица рецептов (блюд)
CREATE TABLE recipes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL UNIQUE,
  description TEXT,
  cost REAL NOT NULL CHECK (cost >= 0),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Таблица ингредиентов (из прошлого вопроса)
CREATE TABLE ingredients (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL UNIQUE,
  price REAL NOT NULL CHECK (price >= 0),
  -- REAL используется для цен (числа с плавающей точкой)
  unit TEXT NOT NULL,
  -- граммы, мл, шт и т.д.
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 3. Связующая таблица (Составной рецепта)
CREATE TABLE recipe_ingredients (
  recipe_id INTEGER,
  ingredient_id INTEGER,
  quantity REAL NOT NULL CHECK (quantity > 0),
  -- Сколько нужно ингредиента
  -- Составной первичный ключ (гарантирует, что один ингредиент не добавится в один рецепт дважды)
  PRIMARY KEY (recipe_id, ingredient_id),
  -- Внешние ключи со связями
  FOREIGN KEY (recipe_id) REFERENCES recipes (id) ON DELETE CASCADE,
  -- Если удалить рецепт, его состав удалится автоматически
  FOREIGN KEY (ingredient_id) REFERENCES ingredients (id) ON DELETE RESTRICT -- Не позволит удалить ингредиент, если он используется в каком-то рецепте
);

CREATE TABLE sales (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  recipe_id INTEGER,
  customer_id INTEGER,
  cost REAL NOT NULL CHECK (cost >= 0),
  cost_price REAL NOT NULL CHECK (cost_price >= 0),
  quantity INTEGER NOT NULL CHECK (quantity > 0),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (recipe_id) REFERENCES recipes (id) ON DELETE CASCADE,
  FOREIGN KEY (customer_id) REFERENCES customers (id) ON DELETE CASCADE
);

CREATE TRIGGER IF NOT EXISTS update_ingredients_timestamp
AFTER
UPDATE
  ON ingredients FOR EACH ROW BEGIN
UPDATE
  ingredients
SET
  updated_at = STRFTIME ('%Y-%m-%d %H:%M:%S', 'NOW')
WHERE
  id = OLD.id;

END;