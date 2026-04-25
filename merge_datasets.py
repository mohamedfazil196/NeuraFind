import pandas as pd
import re
import os

# --- Configurations ---
MAIN_BRANDS = [
    "Apple", "Samsung", "Google", "OnePlus", "Xiaomi", "Redmi", 
    "Nothing", "Motorola", "Realme", "Vivo", "iQOO", "POCO", "Oppo"
]

DATASETS_DIR = r"x:\fz project\device-recommender\datasets"
MASTER_CSV = os.path.join(DATASETS_DIR, "mobile.csv")
AMAZON_CSV = os.path.join(DATASETS_DIR, "Mobile_Phones_Dataset_Amazon.csv")
FLIPKART_CSV = os.path.join(DATASETS_DIR, "flipkart_mobiles_dataset_2026.csv")

def clean_amazon_price(price_str):
    if pd.isna(price_str) or not isinstance(price_str, str):
        return None
    # Amazon price looks like "359,957..82"
    # Take the part before multiple dots
    parts = price_str.split('.')
    main_part = parts[0].replace(',', '')
    try:
        return float(main_part)
    except:
        return None

def clean_amazon_rating(rating_str):
    if pd.isna(rating_str) or not isinstance(rating_str, str):
        return None
    # Looks like "4.6 out of 5 stars"
    match = re.search(r"(\d+\.\d+)", rating_str)
    if match:
        return float(match.group(1))
    return None

def clean_amazon_reviews(reviews_str):
    if pd.isna(reviews_str) or not isinstance(reviews_str, str):
        return 1000 # Default fallback
    # Looks like "3K+ bought in past month"
    match = re.search(r"(\d+)K", reviews_str, re.I)
    if match:
        return int(match.group(1)) * 1000
    match = re.search(r"(\d+)\+", reviews_str)
    if match:
        return int(match.group(1))
    return 500

def extract_from_title(title, pattern, default=None):
    if pd.isna(title) or not isinstance(title, str):
        return default
    match = re.search(pattern, title, re.I)
    if match:
        return int(match.group(1))
    return default

def process_datasets():
    # 1. Load Original Data to keep
    print("Loading original master dataset...")
    df_master = pd.read_csv(MASTER_CSV)
    
    # 2. Process Amazon Dataset
    print("Processing Amazon dataset...")
    df_amazon = pd.read_csv(AMAZON_CSV)
    # Filter brands (Case insensitive check)
    df_amazon = df_amazon[df_amazon['brand'].str.title().isin(MAIN_BRANDS)]
    
    amazon_cleaned = pd.DataFrame()
    amazon_cleaned['name'] = df_amazon['title'].str.strip().str.slice(stop=100)
    amazon_cleaned['price'] = df_amazon['price'].apply(clean_amazon_price)
    amazon_cleaned['ram'] = df_amazon['ram_gb'].fillna(8) # Fallback to 8GB for missing
    amazon_cleaned['storage'] = df_amazon['storage_gb'].fillna(128)
    amazon_cleaned['camera'] = df_amazon['title'].apply(lambda x: extract_from_title(x, r"(\d+)MP", 50))
    amazon_cleaned['battery'] = df_amazon['title'].apply(lambda x: extract_from_title(x, r"(\d{4})mAh", 5000))
    amazon_cleaned['brand'] = df_amazon['brand'].str.title()
    amazon_cleaned['rating'] = df_amazon['rating'].apply(clean_amazon_rating).fillna(4.2)
    amazon_cleaned['reviews'] = df_amazon['reviews'].apply(clean_amazon_reviews)
    
    # 3. Process Flipkart Dataset
    print("Processing Flipkart dataset...")
    try:
        df_flipkart = pd.read_csv(FLIPKART_CSV)
        # Filter brands
        df_flipkart = df_flipkart[df_flipkart['brand'].str.title().isin(MAIN_BRANDS)]
        
        flipkart_cleaned = pd.DataFrame()
        flipkart_cleaned['name'] = df_flipkart['model'].str.strip()
        flipkart_cleaned['price'] = pd.to_numeric(df_flipkart['price'], errors='coerce')
        flipkart_cleaned['ram'] = pd.to_numeric(df_flipkart['ram'], errors='coerce').fillna(8)
        flipkart_cleaned['storage'] = pd.to_numeric(df_flipkart['rom'], errors='coerce').fillna(128)
        flipkart_cleaned['camera'] = df_flipkart['rear_camera'].apply(lambda x: extract_from_title(str(x), r"(\d+)MP", 50))
        flipkart_cleaned['battery'] = pd.to_numeric(df_flipkart['battery'], errors='coerce').fillna(5000)
        flipkart_cleaned['brand'] = df_flipkart['brand'].str.title()
        flipkart_cleaned['rating'] = pd.to_numeric(df_flipkart['rating'], errors='coerce').fillna(4.2)
        flipkart_cleaned['reviews'] = pd.to_numeric(df_flipkart['reviews_count'], errors='coerce').fillna(1500)
    except Exception as e:
        print(f"Error loading Flipkart: {e}")
        flipkart_cleaned = pd.DataFrame()

    # 4. Merge All
    print("Combining everything...")
    final_df = pd.concat([df_master, amazon_cleaned, flipkart_cleaned], ignore_index=True)
    
    # Final cleaning
    final_df.dropna(subset=['name', 'price'], inplace=True)
    # Remove duplicates by name
    final_df.drop_duplicates(subset=['name'], keep='first', inplace=True)
    # Filter out obvious trash (0 price or very low price)
    final_df = final_df[final_df['price'] > 5000]
    
    # Save back to master
    print(f"Saving {len(final_df)} devices to master dataset...")
    final_df.to_csv(MASTER_CSV, index=False)
    print("Merge complete!")

if __name__ == "__main__":
    process_datasets()
