# models/currency_detection_final.py
import cv2
import numpy as np
import os
import re
import logging
import glob

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
#  Lighting-robust preprocessing
# ─────────────────────────────────────────────────────────────────────────────

def normalize_lighting(gray: np.ndarray) -> np.ndarray:
    """
    Multi-stage pipeline that makes an image look "normally lit" regardless
    of whether it was taken in bright sunlight or a dim room.

    Stages
    ------
    1. Gamma correction  – lifts dark images non-linearly (no effect on
                           already-bright images).
    2. CLAHE             – boosts local contrast so fine note details
                           (patterns, serial numbers) become visible.
    3. Bilateral filter  – smooths noise added by gamma/CLAHE while keeping
                           edges sharp (important for ORB keypoints).
    4. Normalise to 0-255 – ensures the full dynamic range is used, making
                           template correlation scores comparable across
                           lighting conditions.
    """
    # ── Stage 1: adaptive gamma ──────────────────────────────────────────────
    # Compute gamma from mean brightness so dark images get a bigger boost.
    #   mean ≈ 200  → gamma ≈ 0.8  (slightly brighten)
    #   mean ≈ 128  → gamma ≈ 1.0  (no change)
    #   mean ≈  50  → gamma ≈ 1.8  (strongly brighten)
    mean_brightness = float(np.mean(gray))
    if mean_brightness < 10:
        mean_brightness = 10          # avoid log(0)
    gamma = np.log(128.0) / np.log(mean_brightness)
    gamma = float(np.clip(gamma, 0.4, 3.0))

    inv_gamma = 1.0 / gamma
    lut = np.array([
        min(255, int((i / 255.0) ** inv_gamma * 255))
        for i in range(256)
    ], dtype=np.uint8)
    corrected = cv2.LUT(gray, lut)

    # ── Stage 2: CLAHE ───────────────────────────────────────────────────────
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(corrected)

    # ── Stage 3: bilateral denoise ───────────────────────────────────────────
    denoised = cv2.bilateralFilter(enhanced, d=9, sigmaColor=75, sigmaSpace=75)

    # ── Stage 4: full-range normalisation ────────────────────────────────────
    normalised = cv2.normalize(denoised, None, 0, 255, cv2.NORM_MINMAX)

    return normalised


# ─────────────────────────────────────────────────────────────────────────────
#  Detector
# ─────────────────────────────────────────────────────────────────────────────

class CurrencyDetector:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.dataset_path = os.path.join(self.base_dir, 'currency_dataset')
        self.templates = {}
        self.features = {}
        self.denominations = []
        self.orb = cv2.ORB_create(nfeatures=1000)
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        self.load_templates()

    # ── helpers ───────────────────────────────────────────────────────────────

    def extract_denomination(self, filename):
        match = re.match(r'^(\d+)', os.path.basename(filename))
        return int(match.group(1)) if match else None

    def _register_value(self, value):
        if value not in self.templates:
            self.templates[value] = []
            self.features[value] = []
        if value not in self.denominations:
            self.denominations.append(value)

    # ── preprocessing ─────────────────────────────────────────────────────────

    def _preprocess(self, img: np.ndarray) -> np.ndarray:
        """BGR or gray → fully normalised gray."""
        if img is None:
            raise ValueError("_preprocess received None")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()
        return normalize_lighting(gray)

    # ── loading ───────────────────────────────────────────────────────────────

    def load_templates(self):
        print("\n" + "=" * 60)
        print("💰 LOADING CURRENCY DATASET")
        print("=" * 60)
        print(f"📁 {self.dataset_path}")

        if not os.path.exists(self.dataset_path):
            print("❌ Dataset folder not found")
            return

        image_files = []
        for ext in ['*.jpeg', '*.jpg', '*.png']:
            image_files.extend(glob.glob(os.path.join(self.dataset_path, ext)))

        print(f"📸 Found {len(image_files)} images")

        for img_path in image_files:
            value = self.extract_denomination(img_path)
            if not value:
                continue
            img = cv2.imread(img_path)
            if img is None:
                continue

            processed = self._preprocess(img)
            canonical = cv2.resize(processed, (400, 200))

            self._register_value(value)
            self.templates[value].append(canonical)

            kp, des = self.orb.detectAndCompute(processed, None)
            if des is not None:
                self.features[value].append((kp, des))

            print(f"  ✅ ₹{value}  {os.path.basename(img_path)}")

        print("\n📊 SUMMARY:")
        for v in sorted(self.denominations):
            print(f"  ₹{v}: {len(self.templates[v])} templates, "
                  f"{len(self.features[v])} feature sets")
        print("=" * 60 + "\n")

    # ── scoring ───────────────────────────────────────────────────────────────

    def _orb_score(self, des_query, value, dist_thresh=50):
        best = 0
        for (_kp, des_tmpl) in self.features.get(value, []):
            if des_tmpl is None:
                continue
            matches = self.bf.match(des_query, des_tmpl)
            good = sum(1 for m in matches if m.distance < dist_thresh)
            best = max(best, good)
        return best

    def _template_score(self, gray_query, value):
        scores = []
        h_q, w_q = gray_query.shape
        for tmpl in self.templates.get(value, []):
            resized = cv2.resize(tmpl, (w_q, h_q))
            result = cv2.matchTemplate(gray_query, resized, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            scores.append(max_val)
        if not scores:
            return 0.0, 0.0
        return float(np.mean(scores)), float(max(scores))

    def _composite_score(self, gray_query, des_query, value, orb_norm=40):
        orb_c = self._orb_score(des_query, value) if des_query is not None else 0
        avg_t, max_t = self._template_score(gray_query, value)
        orb_n = min(1.0, orb_c / orb_norm)
        score = orb_n * 0.40 + max_t * 0.35 + avg_t * 0.25
        return score, orb_c, avg_t, max_t

    # ── 100 vs 500 disambiguation ─────────────────────────────────────────────

    def _disambiguate_100_500(self, gray_query, des_query):
        """
        FIX: brightness bias REMOVED — after normalize_lighting() both notes
        will have similar mean brightness, making that cue useless/harmful.
        Uses feature matching + edge density tie-breaker only.
        """
        print("\n🔍 DISAMBIGUATING ₹100 vs ₹500")

        s100, orb100, at100, mt100 = self._composite_score(gray_query, des_query, 100)
        s500, orb500, at500, mt500 = self._composite_score(gray_query, des_query, 500)

        print(f"  ₹100: composite={s100:.3f}  ORB={orb100}  tmpl_avg={at100:.3f}  tmpl_max={mt100:.3f}")
        print(f"  ₹500: composite={s500:.3f}  ORB={orb500}  tmpl_avg={at500:.3f}  tmpl_max={mt500:.3f}")

        edges = cv2.Canny(gray_query, 50, 150)
        edge_density = float(np.sum(edges > 0)) / edges.size
        print(f"  Edge density: {edge_density:.4f}")

        TIE = 0.05
        if abs(s100 - s500) < TIE:
            # ₹500 has denser intaglio printing
            winner, conf = (500, s500) if edge_density > 0.12 else (100, s100)
            print(f"  Tie-break via edge density → ₹{winner}")
        elif s100 > s500:
            winner, conf = 100, s100
        else:
            winner, conf = 500, s500

        return winner, conf

    # ── main detection ────────────────────────────────────────────────────────

    def detect_currency(self, image_path):
        try:
            img = cv2.imread(image_path)
            if img is None:
                return {'success': False, 'error': 'Cannot read image'}
            if not self.denominations:
                return {'success': False, 'error': 'No templates loaded'}

            raw_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            print(f"🌓 Brightness BEFORE normalisation: {np.mean(raw_gray):.1f}")

            gray = self._preprocess(img)
            print(f"🌕 Brightness AFTER  normalisation: {np.mean(gray):.1f}")

            kp_query, des_query = self.orb.detectAndCompute(gray, None)
            print(f"🔍 Query keypoints: {len(kp_query) if kp_query else 0}")

            all_scores = {}
            for value in self.denominations:
                composite, orb_c, avg_t, max_t = self._composite_score(
                    gray, des_query, value)
                all_scores[value] = composite
                print(f"  ₹{value:>4}: composite={composite:.3f}  "
                      f"ORB={orb_c}  tmpl_avg={avg_t:.3f}  tmpl_max={max_t:.3f}")

            ranked = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
            best_value, best_score = ranked[0]

            top_values = {v for v, _ in ranked[:2]}
            if {100, 500}.issubset(top_values) and (ranked[0][1] - ranked[1][1]) < 0.10:
                best_value, best_score = self._disambiguate_100_500(gray, des_query)

            MIN_CONFIDENCE = 0.15
            if best_score < MIN_CONFIDENCE:
                return {
                    'success': False,
                    'error': f'Low confidence ({best_score:.3f}) — image unclear or not currency'
                }

            print(f"\n✅ DETECTED: ₹{best_value}  confidence={best_score:.3f}")
            return {
                'success': True,
                'value': best_value,
                'denomination': f'₹{best_value}',
                'confidence': round(best_score, 3),
                'method': 'composite',
                'all_scores': {str(v): round(s, 3) for v, s in ranked}
            }

        except Exception as e:
            logger.error(f"Detection error: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    # ── base64 entry point ────────────────────────────────────────────────────

    def detect_from_base64(self, base64_string):
        import base64
        try:
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            image_bytes = base64.b64decode(base64_string)
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                return {'success': False, 'error': 'Could not decode image'}

            uploads_dir = os.path.join(self.base_dir, 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            temp_path = os.path.join(uploads_dir, 'temp_currency.jpg')
            cv2.imwrite(temp_path, img)

            result = self.detect_currency(temp_path)
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return result

        except Exception as e:
            logger.error(f"base64 error: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}