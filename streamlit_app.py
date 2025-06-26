import streamlit as st
from openai import OpenAI
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize client as None - will be created when needed
client = None

def calculate_bmr(weight: float, height: float, age: int, sex: str, unit: str) -> float:
    """Calculate Basal Metabolic Rate using Mifflin-St Jeor Equation."""
    # Convert to metric if needed
    if unit == "Imperial":
        weight_kg = weight * 0.453592  # lbs to kg
        height_cm = height * 2.54     # inches to cm
    else:
        weight_kg = weight
        height_cm = height
    
    if sex == "Male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:  # Female or Other
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    
    return bmr

def calculate_tdee(bmr: float, activity_level: str, training_days: int) -> float:
    """Calculate Total Daily Energy Expenditure."""
    activity_multipliers = {
        "Sedentary": 1.2,
        "Lightly active": 1.375,
        "Moderately active": 1.55,
        "Very active": 1.725
    }
    
    base_multiplier = activity_multipliers.get(activity_level, 1.375)
    
    # Adjust for training frequency
    training_adjustment = 1 + (training_days * 0.05)  # 5% per training day
    
    return bmr * base_multiplier * training_adjustment

def calculate_target_calories_and_macros(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate target calories and macronutrients based on goals."""
    bmr = calculate_bmr(
        user_data['weight'], 
        user_data['height'], 
        user_data['age'], 
        user_data['sex'], 
        user_data['unit']
    )
    
    tdee = calculate_tdee(bmr, user_data['activity'], user_data['days'])
    
    # Adjust calories based on goal
    goal_adjustments = {
        "Lose fat": -500,        # 500 calorie deficit
        "Build muscle": 300,     # 300 calorie surplus
        "Re-comp": 0,           # Maintenance
        "General health": -100   # Slight deficit for health
    }
    
    target_calories = tdee + goal_adjustments.get(user_data['goal'], 0)
    
    # Calculate macros based on goal and diet style
    if user_data['goal'] == "Build muscle":
        protein_ratio = 0.30
        fat_ratio = 0.25
        carb_ratio = 0.45
    elif user_data['goal'] == "Lose fat":
        protein_ratio = 0.35
        fat_ratio = 0.30
        carb_ratio = 0.35
    else:  # Re-comp or General health
        protein_ratio = 0.25
        fat_ratio = 0.30
        carb_ratio = 0.45
    
    # Adjust for diet style
    if user_data['diet'] == "Keto":
        protein_ratio = 0.25
        fat_ratio = 0.70
        carb_ratio = 0.05
    elif user_data['diet'] == "Vegan":
        protein_ratio = 0.20
        fat_ratio = 0.25
        carb_ratio = 0.55
    
    protein_calories = target_calories * protein_ratio
    fat_calories = target_calories * fat_ratio
    carb_calories = target_calories * carb_ratio
    
    # Convert to grams (protein: 4 cal/g, fat: 9 cal/g, carbs: 4 cal/g)
    protein_grams = protein_calories / 4
    fat_grams = fat_calories / 9
    carb_grams = carb_calories / 4
    
    return {
        'bmr': round(bmr),
        'tdee': round(tdee),
        'target_calories': round(target_calories),
        'protein_grams': round(protein_grams),
        'fat_grams': round(fat_grams),
        'carb_grams': round(carb_grams),
        'protein_calories': round(protein_calories),
        'fat_calories': round(fat_calories),
        'carb_calories': round(carb_calories)
    }

def create_workout_prompt(user_data: Dict[str, Any]) -> str:
    """Create a structured prompt for OpenAI based on user input."""
    
    # Calculate nutrition targets
    nutrition_data = calculate_target_calories_and_macros(user_data)
    
    # Convert equipment list to string
    equipment = ", ".join(user_data['equip']) if user_data['equip'] else "No equipment specified"
    
    # Convert training style list to string
    training_styles = ", ".join(user_data['style']) if user_data['style'] else "No specific style"
    
    prompt = f"""
    Create a comprehensive, personalized workout and nutrition plan based on the following user information:

    PERSONAL INFO:
    - Name: {user_data['name']}
    - Age: {user_data['age']}
    - Sex: {user_data['sex']}
    - Height: {user_data['height']} {'inches' if user_data['unit'] == 'Imperial' else 'cm'}
    - Weight: {user_data['weight']} {'lbs' if user_data['unit'] == 'Imperial' else 'kg'}

    FITNESS GOALS & EXPERIENCE:
    - Primary Goal: {user_data['goal']}
    - Training Experience: {user_data['level']}
    - Training Days per Week: {user_data['days']}
    - Workout Duration: {user_data['minutes']} minutes per session
    - Activity Level: {user_data['activity']}

    CALCULATED NUTRITION TARGETS:
    - BMR (Basal Metabolic Rate): {nutrition_data['bmr']} calories/day
    - TDEE (Total Daily Energy Expenditure): {nutrition_data['tdee']} calories/day
    - Target Daily Calories: {nutrition_data['target_calories']} calories
    - Target Protein: {nutrition_data['protein_grams']}g ({nutrition_data['protein_calories']} calories)
    - Target Carbohydrates: {nutrition_data['carb_grams']}g ({nutrition_data['carb_calories']} calories)
    - Target Fats: {nutrition_data['fat_grams']}g ({nutrition_data['fat_calories']} calories)

    EQUIPMENT & PREFERENCES:
    - Available Equipment: {equipment}
    - Training Style Preferences: {training_styles}
    - Diet Style: {user_data['diet']}

    LIMITATIONS & CONSIDERATIONS:
    - Allergies/Injuries: {user_data['issues'] if user_data['issues'] else 'None specified'}
    - Food Dislikes: {user_data['dislikes'] if user_data['dislikes'] else 'None specified'}
    - Medical Conditions: {user_data['medical'] if user_data['medical'] else 'None specified'}

    Please provide a detailed plan that includes:

    1. WORKOUT PLAN:
       - Weekly training split with specific days
       - Detailed exercises with sets, reps, and rest periods
       - Progression guidelines over 4-8 weeks
       - Warm-up and cool-down routines

    2. COMPREHENSIVE NUTRITION PLAN:
       - Meal timing strategy (pre/post workout, daily schedule)
       - Specific food recommendations for each macro target
       - Sample meal plans for 3-5 days aligned with their diet style
       - Hydration guidelines
       - Supplement recommendations (if appropriate)
       - Meal prep tips and grocery list suggestions

    3. LIFESTYLE INTEGRATION:
       - Recovery and sleep recommendations
       - Stress management tips
       - Progress tracking methods
       - Modifications for busy days
       - Long-term sustainability strategies

    4. SAFETY & MODIFICATIONS:
       - Exercise modifications for any mentioned limitations
       - Warning signs to watch for
       - When to rest or deload

    Use the calculated nutrition targets as the foundation for all nutrition recommendations. Format the response with clear headers, bullet points, and practical actionable advice.
    """
    
    return prompt

def generate_workout_plan(user_data: Dict[str, Any], api_key: str) -> str:
    """Generate workout plan using OpenAI API."""
    try:
        # Debug: Show API key info (first 10 and last 4 characters for security)
        if api_key:
            key_preview = f"{api_key[:10]}...{api_key[-4:]}" if len(api_key) > 14 else "Key too short"
            st.info(f"🔑 Using API key: {key_preview} (Length: {len(api_key)} characters)")
        
        # Create OpenAI client with the provided API key
        openai_client = OpenAI(api_key=api_key)
        
        prompt = create_workout_prompt(user_data)
        
        response = openai_client.chat.completions.create(
            model="gpt-4",  # or "gpt-3.5-turbo" for faster/cheaper option
            messages=[
                {
                    "role": "system", 
                    "content": "You are a certified personal trainer and nutritionist with expertise in creating safe, effective, and personalized workout plans. Always prioritize safety and proper form."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        error_msg = str(e)
        
        # Enhanced error handling with specific guidance
        if "401" in error_msg or "invalid_api_key" in error_msg:
            return f"""
            🚫 **API Key Error Detected!**
            
            **Error Details:** {error_msg}
            
            **Common Solutions:**
            1. **Check your API key format** in Streamlit Cloud secrets:
               - Should be: `OPENAI_API_KEY = "sk-proj-your-full-key-here"`
               - No extra spaces, quotes, or line breaks
            
            2. **Verify your API key is active:**
               - Go to https://platform.openai.com/api-keys
               - Make sure your key hasn't expired
               - Check if you have billing set up
            
            3. **Copy the key carefully:**
               - Select the entire key (they're very long!)
               - Don't include any extra characters
            
            4. **Restart your Streamlit app** after updating secrets
            
            Need help? The key should start with `sk-proj-` and be about 164 characters long.
            """
        else:
            return f"Error generating workout plan: {error_msg}\n\nPlease check your OpenAI API key and try again."

# Streamlit App Title
st.title("🏋️ AI Fitness Coach")
st.markdown("Get your personalized workout plan powered by AI!")

# Get the API key from Streamlit secrets or environment variables
try:
    current_api_key = st.secrets["OPENAI_API_KEY"]
except (KeyError, FileNotFoundError):
    current_api_key = os.getenv("OPENAI_API_KEY")

unit = st.radio("Units", ["Imperial", "Metric"], horizontal=True)

with st.form("intake"):
    name  = st.text_input("Name")
    email = st.text_input("Email for delivery")
    age   = st.number_input("Age", 13, 80, step=1)

    sex   = st.radio("Sex", ["Male", "Female", "Other"], horizontal=True)

    if unit == "Imperial":
        height = st.number_input("Height (inches)")
        weight = st.number_input("Weight (lbs)")
    else:
        height = st.number_input("Height (cm)")
        weight = st.number_input("Weight (kg)")

    goal     = st.selectbox("Primary goal", ["Lose fat", "Build muscle", "Re-comp", "General health"])
    level    = st.radio("Training experience", ["Beginner", "Intermediate", "Advanced"], horizontal=True)
    days     = st.slider("Training days per week", 2, 7, 4)
    equip    = st.multiselect("Equipment available", ["Body-weight", "Bands", "DBs", "Barbell", "Machines"])
    diet     = st.selectbox("Diet style", ["Omnivore", "Vegetarian", "Vegan", "Keto", "None"])
    issues   = st.text_area("Allergies / injuries (optional)")

    with st.expander("Advanced tweaks (optional)"):
        activity = st.radio("Activity level", ["Sedentary", "Lightly active", "Moderately active", "Very active"])
        minutes  = st.slider("Time per workout (minutes)", 20, 90, 45)
        style    = st.multiselect(
            "Describe your training style",
            ["Bodybuilder (hypertrophy)", "Powerlifter (strength)",
             "CrossFit / functional fitness", "Science-based / periodized",
             "Calisthenics / street workout", "Endurance / hybrid", "Other"]
        )
        dislikes = st.text_input("Food dislikes")
        medical  = st.text_area("Medical conditions / meds")

    submitted = st.form_submit_button("Generate my plan")

# Handle form submission
if submitted:
    # Validate required fields
    if not name or not email or not age or not height or not weight:
        st.error("Please fill in all required fields (Name, Email, Age, Height, Weight)")
    elif not current_api_key:
        st.error("🔑 **OpenAI API Key Required!** Please set your API key in Streamlit Cloud secrets. Go to your app settings → Secrets tab → Add: `OPENAI_API_KEY = \"your-api-key-here\"`")
    else:
        # Prepare user data
        user_data = {
            'name': name,
            'email': email,
            'age': age,
            'sex': sex,
            'height': height,
            'weight': weight,
            'unit': unit,
            'goal': goal,
            'level': level,
            'days': days,
            'equip': equip,
            'diet': diet,
            'issues': issues,
            'activity': activity,
            'minutes': minutes,
            'style': style,
            'dislikes': dislikes,
            'medical': medical
        }
        
        # Show loading spinner
        with st.spinner("🤖 AI is creating your personalized workout plan..."):
            workout_plan = generate_workout_plan(user_data, current_api_key)
        
        # Display the generated plan
        st.success("🎉 Your personalized workout plan is ready!")
        
        # Calculate nutrition data for display
        nutrition_data = calculate_target_calories_and_macros(user_data)
        
        # Create tabs for better organization
        tab1, tab2, tab3 = st.tabs(["📋 Complete Plan", "🍎 Nutrition Targets", "📊 Your Profile"])
        
        with tab1:
            st.markdown("### Your AI-Generated Workout & Nutrition Plan")
            st.markdown(workout_plan)
            
            # Add download button
            st.download_button(
                label="📥 Download Your Complete Plan",
                data=workout_plan,
                file_name=f"{name.replace(' ', '_')}_complete_fitness_plan.txt",
                mime="text/plain"
            )
        
        with tab2:
            st.markdown("### 🎯 Your Personalized Nutrition Targets")
            
            # Calorie breakdown
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🔥 Target Calories", f"{nutrition_data['target_calories']:,}")
                st.caption(f"BMR: {nutrition_data['bmr']:,} | TDEE: {nutrition_data['tdee']:,}")
            
            with col2:
                st.metric("💪 Protein", f"{nutrition_data['protein_grams']}g")
                st.caption(f"{nutrition_data['protein_calories']} calories")
            
            with col3:
                st.metric("🍞 Carbs", f"{nutrition_data['carb_grams']}g")
                st.caption(f"{nutrition_data['carb_calories']} calories")
            
            # Fat in a separate row for better spacing
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🥑 Fats", f"{nutrition_data['fat_grams']}g")
                st.caption(f"{nutrition_data['fat_calories']} calories")
            
            # Macro breakdown chart
            st.markdown("#### 📊 Macro Distribution")
            macro_data = {
                'Macronutrient': ['Protein', 'Carbs', 'Fats'],
                'Grams': [nutrition_data['protein_grams'], nutrition_data['carb_grams'], nutrition_data['fat_grams']],
                'Calories': [nutrition_data['protein_calories'], nutrition_data['carb_calories'], nutrition_data['fat_calories']]
            }
            
            col1, col2 = st.columns(2)
            with col1:
                st.bar_chart(dict(zip(macro_data['Macronutrient'], macro_data['Grams'])))
                st.caption("Macronutrients in Grams")
            
            with col2:
                st.bar_chart(dict(zip(macro_data['Macronutrient'], macro_data['Calories'])))
                st.caption("Macronutrients in Calories")
            
            # Goal-specific advice
            st.markdown("#### 🎯 Goal-Specific Nutrition Tips")
            if goal == "Lose fat":
                st.info("💡 **Fat Loss Focus**: You're in a 500-calorie deficit. Prioritize protein to maintain muscle mass while losing fat. Consider eating protein at every meal.")
            elif goal == "Build muscle":
                st.info("💡 **Muscle Building Focus**: You're in a 300-calorie surplus. Focus on post-workout nutrition and spread protein throughout the day for optimal muscle protein synthesis.")
            elif goal == "Re-comp":
                st.info("💡 **Body Recomposition**: You're eating at maintenance. Focus on nutrient timing - more carbs around workouts, adequate protein throughout the day.")
            else:
                st.info("💡 **General Health**: You're in a slight deficit for overall health. Focus on nutrient-dense whole foods and consistent meal timing.")
            
            # Diet-specific notes
            if diet == "Keto":
                st.warning("🥑 **Keto Diet**: Your macros are adjusted for ketosis (70% fat, 25% protein, 5% carbs). Focus on healthy fats and time your small carb intake around workouts.")
            elif diet == "Vegan":
                st.success("🌱 **Vegan Diet**: Focus on complete proteins (quinoa, hemp, soy) and B12 supplementation. Consider plant-based protein powder to meet targets.")
            elif diet == "Vegetarian":
                st.success("🥛 **Vegetarian Diet**: Include eggs, dairy, and legumes for complete proteins. Greek yogurt and cottage cheese are excellent protein sources.")
        
        with tab3:
            st.markdown("### Your Fitness Profile")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Age", f"{age} years")
                st.metric("Height", f"{height} {'in' if unit == 'Imperial' else 'cm'}")
                st.metric("Weight", f"{weight} {'lbs' if unit == 'Imperial' else 'kg'}")
                st.metric("Training Days", f"{days} per week")
                st.metric("Session Length", f"{minutes} minutes")
            
            with col2:
                st.write(f"**Primary Goal:** {goal}")
                st.write(f"**Experience Level:** {level}")
                st.write(f"**Activity Level:** {activity}")
                st.write(f"**Diet Style:** {diet}")
                st.write(f"**Available Equipment:** {', '.join(equip) if equip else 'None specified'}")
                if style:
                    st.write(f"**Training Style:** {', '.join(style)}")
            
            # Additional info if provided
            if issues or dislikes or medical:
                st.markdown("#### 📝 Additional Considerations")
                if issues:
                    st.write(f"**Allergies/Injuries:** {issues}")
                if dislikes:
                    st.write(f"**Food Dislikes:** {dislikes}")
                if medical:
                    st.write(f"**Medical Conditions:** {medical}")

# Add footer
st.markdown("---")
st.markdown("*Disclaimer: This AI-generated workout plan is for informational purposes only. Consult with a healthcare professional before starting any new exercise program.*")
