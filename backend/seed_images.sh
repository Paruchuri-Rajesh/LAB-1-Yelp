#!/bin/bash
# Download food images from Unsplash for each cuisine type
DIR="/Users/rajesh_paruchuri/Desktop/DS-sem-2/LAB-1/backend/uploads/restaurants"
mkdir -p "$DIR"

# Food search terms mapped to cuisine
declare -a TERMS=(
  "italian-pasta"
  "chinese-food"
  "mexican-tacos"
  "indian-curry"
  "japanese-sushi"
  "american-burger"
  "thai-food"
  "french-cuisine"
  "korean-bbq"
  "mediterranean-food"
  "pizza"
  "noodles"
  "steak"
  "seafood"
  "salad"
  "dessert"
  "breakfast"
  "grilled-meat"
  "soup"
  "sandwich"
)

echo "Downloading 100 food images..."
for i in $(seq 1 100); do
  TERM_INDEX=$(( (i - 1) % ${#TERMS[@]} ))
  TERM="${TERMS[$TERM_INDEX]}"
  FILE="$DIR/restaurant_${i}.png"

  # Use a unique sig per image to get different results
  URL="https://source.unsplash.com/800x500/?${TERM}&sig=${i}"

  echo "[$i/100] Downloading ${TERM} image..."
  curl -s -L -o "$FILE" "$URL"

  # Check if file is valid (at least 10KB)
  SIZE=$(wc -c < "$FILE" 2>/dev/null)
  if [ "$SIZE" -lt 10000 ]; then
    echo "  Retrying with fallback..."
    curl -s -L -o "$FILE" "https://loremflickr.com/800/500/food,${TERM}"
  fi
done

echo "Done downloading images!"
