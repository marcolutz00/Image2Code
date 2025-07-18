import cv2


# Hypothesis CC: Size of Fonts different
def calculate_size_fonts(df, image_path):
    """
    Check if size of fonts different
    Here only difference between large and small fonts accoridng to WCAG criteria
    """
    # Distribution small, large fonts
    original_img = cv2.imread(image_path)
    height, width = original_img.shape[:2]

    df["is_large"] = df["bbox"].apply(lambda bbox: bbox[3] * height >= 24)

    amount_large_fonts = df["is_large"].sum()
    amount_small_fonts = len(df) - amount_large_fonts

    return amount_large_fonts, amount_small_fonts