import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

/// Centralized localization for Tamil (ta), English (en), and Hindi (hi).
class AppLocalizations {
  final Locale locale;
  AppLocalizations(this.locale);

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations) ??
        AppLocalizations(const Locale('en'));
  }

  static const LocalizationsDelegate<AppLocalizations> delegate = _AppLocalizationsDelegate();

  static final Map<String, Map<String, String>> _localizedValues = {
    'en': {
      // General & Navigation
      'app_title': 'TN Fertilizer Optimizer',
      'app_subtitle': 'AI-Based Soil-Specific Fertilizer Recommendation & Yield Prediction',
      'home': 'Home',
      'soil_reports': 'Soil Reports',
      'fertilizer': 'Fertilizer',
      'yield_and_weather': 'Yield & Weather',
      'history': 'History',
      'profile': 'Profile',
      'settings': 'Settings',
      'help': 'Help & Guide',
      'about': 'About',
      'notifications': 'Notifications',
      'back': 'Back',
      'continue_btn': 'Continue',
      'cancel': 'Cancel',
      'save': 'Save',
      'submit': 'Submit',
      'retry': 'Try Again',
      'loading': 'Please wait...',
      'success': 'Success',
      'error': 'Error',
      'download': 'Download',
      'share': 'Share',

      // Languages
      'select_language': 'Select Your Language',
      'english': 'English',
      'tamil': 'தமிழ் (Tamil)',
      'hindi': 'हिन्दी (Hindi)',
      'language_desc': 'You can change this anytime from Settings.',

      // Auth
      'login_title': 'Farmer Login',
      'login_subtitle': 'Access your soil reports and recommendations',
      'email_or_phone': 'Email or Mobile Number',
      'password': 'Password',
      'login_btn': 'Log In',
      'no_account': "Don't have an account?",
      'register_here': 'Register as a Farmer',
      'register_title': 'Farmer Registration',
      'full_name': 'Full Name',
      'district': 'District',
      'village': 'Village / Town',
      'preferred_language': 'Preferred Language',
      'register_btn': 'Create Account',
      'already_have_account': 'Already registered?',
      'logout': 'Log Out',

      // Dashboard
      'greeting': 'Vanakkam, Farmer!',
      'dashboard_quick_actions': 'Quick Actions',
      'upload_card': 'Upload Soil Card',
      'get_recommendation': 'Fertilizer Optimizer',
      'predict_yield': 'Predict Crop Yield',
      'weather_advisory': 'Weather Advisory',
      'recent_recommendations': 'Recent Recommendations',
      'no_recent_rec': 'No recommendations generated yet. Upload your soil card to start.',
      'start_now': 'Start Now',

      // Soil Upload & OCR
      'upload_soil_title': 'Soil Health Card Upload',
      'upload_instruction': 'Upload your Soil Health Card (PDF or Photo) to automatically extract NPK and soil parameters.',
      'upload_pdf': 'Upload PDF Report',
      'upload_image': 'Choose Image / Photo',
      'take_photo': 'Take Photo with Camera',
      'file_size_limit': 'Maximum file size: 10 MB',
      'processing_ocr': 'Reading and extracting soil report...',
      'ocr_success': 'Values extracted from soil report',
      'verify_soil_title': 'Verify Soil Test Values',
      'verify_soil_desc': 'Please check the values read from your report and correct any mistakes.',
      'nitrogen': 'Available Nitrogen (N)',
      'phosphorus': 'Available Phosphorus (P)',
      'potassium': 'Available Potassium (K)',
      'ph': 'Soil pH',
      'ec': 'Electrical Conductivity (EC)',
      'organic_carbon': 'Organic Carbon (OC)',
      'p_method': 'Phosphorus Test Method (Olsen / Bray)',
      'confirm_and_continue': 'Confirm & Continue',
      'manual_entry': 'Enter Values Manually',

      // Farm & Crop
      'farm_details_title': 'Farm & Crop Details',
      'farm_area': 'Farm Area',
      'area_unit': 'Area Unit',
      'irrigation_method': 'Irrigation Type',
      'soil_series': 'Soil Series (TNAU Class)',
      'select_crop': 'Target Crop',
      'season': 'Cropping Season',
      'previous_crop': 'Previous Crop Grown',
      'fym_applied': 'Farmyard Manure (FYM Applied)',
      'previous_fertilizer': 'Previous Fertilizers & Manure',
      'add_fertilizer_record': 'Add Previously Applied Fertilizer',

      // Recommendations & NPK
      'npk_title': 'Nutrient Requirements (NPK)',
      'npk_desc': 'Calculated deterministically using official TNAU STCR-IPNS regression equations.',
      'nutrient_breakdown_title': 'Agronomic Nutrient Breakdown',
      'crop_requirement': 'Crop Requirement',
      'soil_supply_credit': 'Soil Test Supply Deduction',
      'fym_credit': 'Organic Manure (FYM) Credit',
      'previous_crop_credit': 'Previous Legume Crop Credit',
      'previous_fertilizer_residual': 'Previous Fertilizer Residual',
      'final_net_dose': 'Final Chemical Dose to Apply',
      'card_comparison_title': 'Soil Health Card Printed vs Calculated Need',
      'card_prints': 'Card Printed Dose',
      'calculated_need': 'Soil-Test Calculated Need',
      'difference': 'Difference',
      'not_printed_on_card': 'Not printed on card',
      'optimal_plan_title': 'Cost-Optimized Fertilizer Plan',
      'optimal_plan_desc': 'Calculated using Linear Programming to fulfill 100% nutrient requirements at lowest retail cost.',
      'bags_needed': 'Bags Required',
      'estimated_cost': 'Total Estimated Cost',
      'application_schedule': 'Split Application Schedule',
      'basal_stage': 'Basal Application (At Sowing/Planting)',
      'tillering_stage': 'Tillering / Vegetative Stage',
      'panicle_stage': 'Panicle Initiation / Flowering',
      'save_recommendation': 'Save Recommendation',
      'download_pdf': 'Download Official PDF Report',

      // Yield Prediction
      'yield_title': 'District Crop Yield Benchmark',
      'yield_disclaimer': 'District benchmark, not a prediction for your field. Derived from historical Season & Crop Reports.',
      'estimated_district_yield': 'District Benchmark (not a prediction for your field)',
      'rainfall_features': 'Seasonal Rainfall (mm)',

      // Weather & Sustainability
      'weather_title': 'Agro-Weather Guidance',
      'weather_advice': 'Fertilizer Application Advice',
      'sustainability_title': 'Sustainability & Soil Health',
      'nutrient_balance': 'Nutrient Sufficiency & Balance',

      // Help & About
      'help_title': 'Farmer Guidance & FAQs',
      'about_title': 'About the Project (SIH1639)',

      // Domain Error Messages (Phase 6 Requirements)
      'upload_failure': 'Unable to upload the soil report. Please try again.',
      'ocr_failure': 'Unable to extract soil values. Please review the report.',
      'missing_values': 'Some required soil values are missing.',
      'unsupported_crop': 'A verified fertilizer recommendation rule is not available for this crop.',
      'optimization_failure': 'Unable to calculate a valid fertilizer combination with the available product data and constraints.',
      'weather_failure': 'Weather information is currently unavailable. You can continue with the soil-based workflow.',
      'yield_failure': 'Unable to generate the yield estimate. Please check the inputs and try again.',

      // Password Recovery
      'forgot_password': 'Forgot Password?',
      'forgot_password_desc': 'Enter your registered email or phone to reset your password.',
      'reset_instruction': 'Password reset instructions have been sent to your registered contact.',
    },
    'ta': {
      // General & Navigation
      'app_title': 'தமிழ்நாடு உர பரிந்துரை',
      'app_subtitle': 'மண் பரிசோதனை அடிப்படையிலான உகந்த உர பரிந்துரை மற்றும் விளைச்சல் கணிப்பு',
      'home': 'முகப்பு',
      'soil_reports': 'மண் அறிக்கை',
      'fertilizer': 'உர பரிந்துரை',
      'yield_and_weather': 'விளைச்சல் & வானிலை',
      'history': 'வரலாறு',
      'profile': 'சுயவிவரம்',
      'settings': 'அமைப்புகள்',
      'help': 'உதவி வழிகாட்டி',
      'about': 'பற்றி',
      'notifications': 'அறிவிப்புகள்',
      'back': 'பின்செல்',
      'continue_btn': 'தொடர்க',
      'cancel': 'ரத்துசெய்',
      'save': 'சேமி',
      'submit': 'சமர்ப்பி',
      'retry': 'மீண்டும் முயற்சி செய்க',
      'loading': 'தயவுசெய்து காத்திருக்கவும்...',
      'success': 'வெற்றி',
      'error': 'பிழை',
      'download': 'பதிவிறக்கு',
      'share': 'பகிர்',

      // Languages
      'select_language': 'உங்கள் மொழியைத் தேர்வுசெய்யவும்',
      'english': 'English',
      'tamil': 'தமிழ் (Tamil)',
      'hindi': 'हिन्दी (Hindi)',
      'language_desc': 'இதை அமைப்புகள் பக்கத்தில் எப்போது வேண்டுமானாலும் மாற்றலாம்.',

      // Auth
      'login_title': 'விவசாயி உள்நுழைவு',
      'login_subtitle': 'உங்கள் மண் அறிக்கைகள் மற்றும் உர பரிந்துரைகளைப் பார்க்க',
      'email_or_phone': 'மின்னஞ்சல் அல்லது கைபேசி எண்',
      'password': 'கடவுச்சொல்',
      'login_btn': 'உள்நுழைக',
      'no_account': 'கணக்கு இல்லையா?',
      'register_here': 'விவசாயியாக பதிவு செய்யவும்',
      'register_title': 'புதிய விவசாயி பதிவு',
      'full_name': 'முழு பெயர்',
      'district': 'மாவட்டம்',
      'village': 'கிராமம் / ஊர்',
      'preferred_language': 'விருப்ப மொழி',
      'register_btn': 'கணக்கை உருவாக்கு',
      'already_have_account': 'ஏற்கனவே பதிவு செய்துள்ளீர்களா?',
      'logout': 'வெளியேறு',

      // Dashboard
      'greeting': 'வணக்கம் உழவரே!',
      'dashboard_quick_actions': 'விரைவு சேவைகள்',
      'upload_card': 'மண் அட்டை பதிவேற்று',
      'get_recommendation': 'உர பரிந்துரை பெறு',
      'predict_yield': 'விளைச்சல் கணிப்பு',
      'weather_advisory': 'வானிலை ஆலோசனை',
      'recent_recommendations': 'சமீபத்திய பரிந்துரைகள்',
      'no_recent_rec': 'இன்னும் பரிந்துரைகள் உருவாக்கப்படவில்லை. மண் அட்டையை பதிவேற்றவும்.',
      'start_now': 'தொடங்குங்கள்',

      // Soil Upload & OCR
      'upload_soil_title': 'மண் வள அட்டை பதிவேற்றம்',
      'upload_instruction': 'மண் பரிசோதனை அறிக்கையை (PDF அல்லது புகைப்படம்) பதிவேற்றி தழை, மணி, சாம்பல் சத்துக்களை தானாக கண்டறியவும்.',
      'upload_pdf': 'PDF அறிக்கை பதிவேற்று',
      'upload_image': 'புகைப்படத்தை தேர்வு செய்',
      'take_photo': 'கேமரா மூலம் படம் எடு',
      'file_size_limit': 'அதிகபட்ச கோப்பு அளவு: 10 MB',
      'processing_ocr': 'மண் அறிக்கை வாசிக்கப்படுகிறது...',
      'ocr_success': 'மண் அறிக்கையிலிருந்து சத்துக்கள் கண்டறியப்பட்டன',
      'verify_soil_title': 'மண் பரிசோதனை அளவுகளை சரிபார்க்கவும்',
      'verify_soil_desc': 'அறிக்கையிலிருந்து பெறப்பட்ட அளவுகளை சரிபார்த்து திருத்தங்கள் இருப்பின் மாற்றவும்.',
      'nitrogen': 'கிடைக்கும் தழைச்சத்து (N)',
      'phosphorus': 'கிடைக்கும் மணிச்சத்து (P)',
      'potassium': 'கிடைக்கும் சாம்பல்சத்து (K)',
      'ph': 'மண் அமில-காரத்தன்மை (pH)',
      'ec': 'மின் கடத்துதிறன் (EC)',
      'organic_carbon': 'கரிம கார்பன் (OC)',
      'p_method': 'மணிச்சத்து சோதனை முறை (Olsen / Bray)',
      'confirm_and_continue': 'உறுதிசெய்து தொடரவும்',
      'manual_entry': 'நேரடியாக அளவுகளை உள்ளிடுக',

      // Farm & Crop
      'farm_details_title': 'பண்ணை மற்றும் பயிர் விவரங்கள்',
      'farm_area': 'நிலப்பரப்பு',
      'area_unit': 'பரப்பளவு அலகு',
      'irrigation_method': 'பாசன முறை',
      'soil_series': 'மண் வகை (TNAU வகுப்பு)',
      'select_crop': 'பயிர் தேர்வு',
      'season': 'பருவம்',
      'target_yield': 'இலக்கு மகசூல் (டன்/ஹெக்டேர்)',
      'previous_crop': 'முந்தைய பயிர்',
      'fym_applied': 'தொழு உரம் / எரு (டன்/ஹெக்)',
      'previous_fertilizer': 'முந்தைய உர விவரங்கள்',
      'add_fertilizer_record': 'முன்பு பயன்படுத்திய உரத்தை சேர்க்க',

      // Recommendations & NPK
      'npk_title': 'தேவையான ஊட்டச்சத்துக்கள் (NPK)',
      'npk_desc': 'TNAU STCR-IPNS அதிகாரப்பூர்வ கணிதச் சமன்பாடுகள் மூலம் கணக்கிடப்பட்டது.',
      'nutrient_breakdown_title': 'விவசாய ஊட்டச்சத்து விவரப் பிரிப்பு',
      'crop_requirement': 'பயிரின் ஊட்டச்சத்து தேவை',
      'soil_supply_credit': 'மண் பரிசோதனை மூலம் கிடைக்கும் சத்து',
      'fym_credit': 'தொழு உரம் (எரு) மூலம் கிடைக்கும் சத்து',
      'previous_crop_credit': 'முந்தைய பயறு வகை பயிர் ஊட்டம்',
      'previous_fertilizer_residual': 'முன்பு இட்ட உரத்தின் எஞ்சிய சத்து',
      'final_net_dose': 'இட வேண்டிய நிகர ரசாயன உரம்',
      'card_comparison_title': 'அட்டை பரிந்துரை மற்றும் கணக்கிடப்பட்ட தேவை ஒப்பீடு',
      'card_prints': 'அட்டையில் அச்சிடப்பட்ட அளவு',
      'calculated_need': 'மண் பரிசோதனைப்படி தேவை',
      'difference': 'வேறுபாடு',
      'not_printed_on_card': 'அட்டையில் அச்சிடப்படவில்லை',
      'optimal_plan_title': 'குறைந்த செலவு உகந்த உரத் திட்டம்',
      'optimal_plan_desc': 'நேரியல் திட்டமிடல் (LP Solver) மூலம் முழு ஊட்டச்சத்தும் குறைந்த சந்தை விலையில் பெற கணக்கிடப்பட்டது.',
      'bags_needed': 'தேவையான மூட்டைகள்',
      'estimated_cost': 'மொத்த உத்தேச செலவு',
      'application_schedule': 'உரமிடும் கால அட்டவணை',
      'basal_stage': 'அடி உரம் (நடவு/விதைப்பின் போது)',
      'tillering_stage': 'தூர்கட்டும் பருவம்',
      'panicle_stage': 'கதிர் உருவாகும் பருவம்',
      'save_recommendation': 'பரிந்துரையை சேமி',
      'download_pdf': 'அதிகாரப்பூர்வ PDF அறிக்கை பதிவிறக்கு',

      // Yield Prediction
      'yield_title': 'மாவட்ட சராசரி மகசூல் அளவுகோல்',
      'yield_disclaimer': 'மாவட்ட அளவுகோல், உங்கள் நிலத்திற்கான நேரடி முன்கணிப்பு அல்ல. வரலாற்றுப் புள்ளிவிவரங்களின் அடிப்படையிலானது.',
      'estimated_district_yield': 'மாவட்ட அளவுகோல் (உங்கள் நிலத்திற்கான முன்கணிப்பு அல்ல)',
      'rainfall_features': 'பருவமழை அளவு (மி.மீ)',

      // Weather & Sustainability
      'weather_title': 'வானிலை & வேளாண் ஆலோசனை',
      'weather_advice': 'உரமிடும் நேர ஆலோசனை',
      'sustainability_title': 'மண் வளம் & நிலைத்தன்மை',
      'nutrient_balance': 'ஊட்டச்சத்து சமநிலை ஆய்வு',

      // Help & About
      'help_title': 'விவசாயிகளுக்கான வழிகாட்டி & கேள்விகள்',
      'about_title': 'திட்டம் பற்றிய தகவல் (SIH1639)',

      // Domain Error Messages (Phase 6 Requirements)
      'upload_failure': 'மண் அறிக்கையை பதிவேற்ற முடியவில்லை. மீண்டும் முயற்சிக்கவும்.',
      'ocr_failure': 'மண் அளவுகளை பிரித்தெடுக்க முடியவில்லை. அறிக்கையை சரிபார்க்கவும்.',
      'missing_values': 'சில தேவையான மண் பரிசோதனை அளவுகள் விடுபட்டுள்ளன.',
      'unsupported_crop': 'இப்பயிருக்கு சரிபார்க்கப்பட்ட உர பரிந்துரை விதி கிடைக்கவில்லை.',
      'optimization_failure': 'கிடைக்கக்கூடிய உர தயாரிப்புகள் மற்றும் நிபந்தனைகளுடன் சரியான உர கலவையை கணக்கிட முடியவில்லை.',
      'weather_failure': 'வானிலை தகவல் தற்போது கிடைக்கவில்லை. மண் அடிப்படையிலான செயல்முறையை தொடரலாம்.',
      'yield_failure': 'மகசூல் மதிப்பீட்டை உருவாக்க முடியவில்லை. உள்ளீடுகளை சரிபார்த்து மீண்டும் முயற்சிக்கவும்.',

      // Password Recovery
      'forgot_password': 'கடவுச்சொல் மறந்துவிட்டதா?',
      'forgot_password_desc': 'கடவுச்சொல்லை மீட்டமைக்க உங்கள் பதிவு செய்யப்பட்ட மின்னஞ்சல் அல்லது கைபேசி எண்ணை உள்ளிடவும்.',
      'reset_instruction': 'கடவுச்சொல் மீட்டமைப்பு வழிமுறைகள் உங்கள் பதிவு செய்யப்பட்ட தொடர்புக்கு அனுப்பப்பட்டுள்ளன.',
    },
    'hi': {
      // General & Navigation
      'app_title': 'तमिलनाडु उर्वरक अनुकूलक',
      'app_subtitle': 'मृदा-विशिष्ट उर्वरक सिफारिश एवं फसल उपज पूर्वानुमान',
      'home': 'होम',
      'soil_reports': 'मृदा रिपोर्ट',
      'fertilizer': 'उर्वरक',
      'yield_and_weather': 'उपज व मौसम',
      'history': 'इतिहास',
      'profile': 'प्रोफ़ाइल',
      'settings': 'सेटिंग्स',
      'help': 'मार्गदर्शिका',
      'about': 'के बारे में',
      'notifications': 'सूचनाएं',
      'back': 'पीछे',
      'continue_btn': 'आगे बढ़ें',
      'cancel': 'रद्द करें',
      'save': 'सहेजें',
      'submit': 'जमा करें',
      'retry': 'पुनः प्रयास करें',
      'loading': 'कृपया प्रतीक्षा करें...',
      'success': 'सफल',
      'error': 'त्रुटि',
      'download': 'डाउनलोड',
      'share': 'साझा करें',

      // Languages
      'select_language': 'अपनी भाषा चुनें',
      'english': 'English',
      'tamil': 'தமிழ் (Tamil)',
      'hindi': 'हिन्दी (Hindi)',
      'language_desc': 'आप इसे बाद में सेटिंग्स से बदल सकते हैं।',

      // Auth
      'login_title': 'किसान लॉगिन',
      'login_subtitle': 'अपनी मृदा रिपोर्ट और उर्वरक सिफारिशें देखें',
      'email_or_phone': 'ईमेल या मोबाइल नंबर',
      'password': 'पासवर्ड',
      'login_btn': 'लॉगिन करें',
      'no_account': 'खाता नहीं है?',
      'register_here': 'किसान के रूप में पंजीकरण करें',
      'register_title': 'किसान पंजीकरण',
      'full_name': 'पूरा नाम',
      'district': 'ज़िला',
      'village': 'गाँव / कस्बा',
      'preferred_language': 'पसंदीदा भाषा',
      'register_btn': 'खाता बनाएँ',
      'already_have_account': 'पहले से पंजीकृत हैं?',
      'logout': 'लॉगआउट',

      // Dashboard
      'greeting': 'नमस्ते किसान भाई!',
      'dashboard_quick_actions': 'त्वरित सेवाएं',
      'upload_card': 'मृदा कार्ड अपलोड करें',
      'get_recommendation': 'उर्वरक सिफारिश पाएं',
      'predict_yield': 'उपज का अनुमान लगाएं',
      'weather_advisory': 'मौसम सलाह',
      'recent_recommendations': 'हालिया सिफारिशें',
      'no_recent_rec': 'अभी तक कोई सिफारिश नहीं बनी है। शुरू करने के लिए मृदा कार्ड अपलोड करें।',
      'start_now': 'शुरू करें',

      // Soil Upload & OCR
      'upload_soil_title': 'मृदा स्वास्थ्य कार्ड अपलोड',
      'upload_instruction': 'NPK और मृदा पोषक तत्वों को स्वतः पढ़ने के लिए मृदा रिपोर्ट (PDF या फोटो) अपलोड करें।',
      'upload_pdf': 'PDF रिपोर्ट अपलोड करें',
      'upload_image': 'फोटो चुनें',
      'take_photo': 'कैमरे से फोटो लें',
      'file_size_limit': 'अधिकतम फ़ाइल आकार: 10 MB',
      'processing_ocr': 'मृदा रिपोर्ट पढ़ी जा रही है...',
      'ocr_success': 'रिपोर्ट से मान सफलतापूर्वक निकाले गए',
      'verify_soil_title': 'मृदा परीक्षण मान सत्यापित करें',
      'verify_soil_desc': 'रिपोर्ट से पढ़े गए मानों की जांच करें और त्रुटियों को सुधारें।',
      'nitrogen': 'उपलब्ध नाइट्रोजन (N)',
      'phosphorus': 'उपलब्ध फास्फोरस (P)',
      'potassium': 'उपलब्ध पोटाश (K)',
      'ph': 'मृदा pH',
      'ec': 'विद्युत चालकता (EC)',
      'organic_carbon': 'जैविक कार्बन (OC)',
      'p_method': 'फास्फोरस परीक्षण विधि (Olsen / Bray)',
      'confirm_and_continue': 'पुष्टि करें और आगे बढ़ें',
      'manual_entry': 'मान सीधे दर्ज करें',

      // Farm & Crop
      'farm_details_title': 'खेत और फसल विवरण',
      'farm_area': 'खेत का क्षेत्रफल',
      'area_unit': 'क्षेत्रफल इकाई',
      'irrigation_method': 'सिंचाई का प्रकार',
      'soil_series': 'मृदा श्रेणी (TNAU वर्गीकरण)',
      'select_crop': 'फसल का चयन',
      'season': 'मौसम / ऋतु',
      'target_yield': 'लक्षित उपज (टन/हेक्टेयर)',
      'previous_crop': 'पिछली फसल',
      'fym_applied': 'गोबर की खाद / FYM (टन/हेक्टेयर)',
      'previous_fertilizer': 'पूर्व उर्वरक उपयोग',
      'add_fertilizer_record': 'पहले डाले गए उर्वरक जोड़ें',

      // Recommendations & NPK
      'npk_title': 'आवश्यक पोषक तत्व (NPK)',
      'npk_desc': 'आधिकारिक TNAU STCR-IPNS समीकरणों द्वारा गणना की गई।',
      'nutrient_breakdown_title': 'कृषि पोषक तत्व विवरण',
      'crop_requirement': 'फसल की आवश्यकता',
      'soil_supply_credit': 'मिट्टी से आपूर्ति',
      'fym_credit': 'गोबर खाद (FYM) कटौती',
      'previous_crop_credit': 'पिछली दलहनी फसल लाभ',
      'previous_fertilizer_residual': 'पूर्व उर्वरक अवशेष',
      'final_net_dose': 'देय शुद्ध रासायनिक मात्रा',
      'card_comparison_title': 'मृदा स्वास्थ्य कार्ड बनाम गणना की गई आवश्यकता',
      'card_prints': 'कार्ड पर मुद्रित मात्रा',
      'calculated_need': 'गणना की गई आवश्यकता',
      'difference': 'अंतर',
      'not_printed_on_card': 'कार्ड पर मुद्रित नहीं',
      'optimal_plan_title': 'लागत-अनुकूलित उर्वरक योजना',
      'optimal_plan_desc': 'न्यूनतम लागत पर 100% पोषक तत्व आपूर्ति हेतु लीनियर प्रोग्रामिंग (LP) द्वारा अनुकूलित।',
      'bags_needed': 'आवश्यक बोरी संख्या',
      'estimated_cost': 'कुल अनुमानित लागत',
      'application_schedule': 'उर्वरक प्रयोग अनुसूची',
      'basal_stage': 'बुवाई के समय (आधार खुराक)',
      'tillering_stage': 'कल्ले फूटने के समय',
      'panicle_stage': 'बाली निकलने के समय',
      'save_recommendation': 'सिफारिश सहेजें',
      'download_pdf': 'आधिकारिक PDF रिपोर्ट डाउनलोड करें',

      // Yield Prediction
      'yield_title': 'ज़िला औसत फसल उपज मानक',
      'yield_disclaimer': 'ज़िला बेंचमार्क, आपके खेत का सटीक पूर्वानुमान नहीं। ऐतिहासिक ज़िला फसल रिपोर्टों पर आधारित।',
      'estimated_district_yield': 'ज़िला बेंचमार्क (आपके खेत का सटीक पूर्वानुमान नहीं)',
      'rainfall_features': 'मौसमी वर्षा (मिमी)',

      // Weather & Sustainability
      'weather_title': 'मौसम व कृषि सलाह',
      'weather_advice': 'उर्वरक डालने का उचित समय',
      'sustainability_title': 'मृदा स्वास्थ्य व संतुलन',
      'nutrient_balance': 'पोषक तत्व संतुलन विश्लेषण',

      // Help & About
      'help_title': 'किसान गाइड व प्रश्नोत्तरी',
      'about_title': 'परियोजना के बारे में (SIH1639)',

      // Domain Error Messages (Phase 6 Requirements)
      'upload_failure': 'मृदा रिपोर्ट अपलोड करने में असमर्थ। कृपया पुनः प्रयास करें।',
      'ocr_failure': 'मृदा मान निकालने में असमर्थ। कृपया रिपोर्ट की समीक्षा करें।',
      'missing_values': 'कुछ आवश्यक मृदा परीक्षण मान अनुपलब्ध हैं।',
      'unsupported_crop': 'इस फसल के लिए सत्यापित उर्वरक सिफारिश नियम उपलब्ध नहीं है।',
      'optimization_failure': 'उपलब्ध उत्पाद डेटा और बाधाओं के साथ एक मान्य उर्वरक संयोजन की गणना करने में असमर्थ।',
      'weather_failure': 'मौसम की जानकारी वर्तमान में अनुपलब्ध है। आप मृदा-आधारित कार्यप्रवाह जारी रख सकते हैं।',
      'yield_failure': 'उपज अनुमान उत्पन्न करने में असमर्थ। कृपया इनपुट की जांच करें और पुनः प्रयास करें।',

      // Password Recovery
      'forgot_password': 'पासवर्ड भूल गए?',
      'forgot_password_desc': 'अपना पासवर्ड रीसेट करने के लिए अपना पंजीकृत ईमेल या फोन नंबर दर्ज करें।',
      'reset_instruction': 'पासवर्ड रीसेट निर्देश आपके पंजीकृत संपर्क पर भेज दिए गए हैं।',
    }
  };

  String text(String key) {
    final lang = locale.languageCode;
    return _localizedValues[lang]?[key] ?? _localizedValues['en']?[key] ?? key;
  }
}

class _AppLocalizationsDelegate extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();
  @override
  bool isSupported(Locale locale) => ['en', 'ta', 'hi'].contains(locale.languageCode);
  @override
  Future<AppLocalizations> load(Locale locale) => SynchronousFuture<AppLocalizations>(AppLocalizations(locale));
  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

/// Reactive Locale Notifier so changing language in Settings updates the entire app immediately.
class LocaleNotifier extends ChangeNotifier {
  Locale _locale = const Locale('ta'); // Default to Tamil for Tamil Nadu farmers
  Locale get locale => _locale;

  void setLocale(Locale newLocale) {
    if (_locale != newLocale) {
      _locale = newLocale;
      notifyListeners();
    }
  }

  void setLanguageCode(String code) {
    setLocale(Locale(code));
  }
}

final globalLocaleNotifier = LocaleNotifier();
