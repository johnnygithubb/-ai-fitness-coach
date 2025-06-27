import streamlit as st
from openai import OpenAI
import os
import re
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize client as None - will be created when needed
client = None

# Paywall functions removed - now running in free mode for testing

def validate_email(email):
    """Validate email format using regex."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def get_api_key():
    """Get API key from Streamlit secrets or environment variables."""
    api_key = None
    source = "unknown"
    
    # Try Streamlit secrets first (multiple methods)
    try:
        # Method 1: Direct access
        if hasattr(st, 'secrets') and "OPENAI_API_KEY" in st.secrets:
            api_key = st.secrets["OPENAI_API_KEY"]
            source = "Streamlit secrets (direct)"
        # Method 2: Try get method
        elif hasattr(st, 'secrets'):
            api_key = st.secrets.get("OPENAI_API_KEY")
            if api_key:
                source = "Streamlit secrets (get method)"
            else:
                raise KeyError("Not found in secrets")
        else:
            raise KeyError("Streamlit secrets not available")
            
    except (KeyError, FileNotFoundError, AttributeError) as e:
        # Fall back to environment variables
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            source = "Environment variable (.env)"
        else:
            source = f"Not found (secrets error: {str(e)})"
    
    return api_key, source

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
    
    # Get training environment preference
    environment = user_data['environment']
    
    # Convert training style list to string
    training_styles = ", ".join(user_data['style']) if user_data['style'] else "No specific style"
    
    prompt = f"""
    Create a comprehensive, personalized workout and nutrition plan based on the following user information:

    PERSONAL INFO:
    - Email: {user_data['email']}
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

    TRAINING PREFERENCES:
    - Preferred Training Environment: {environment}
    - Training Style Preferences: {training_styles}
    - Diet Style: {user_data['diet']}
    - Session Duration: {user_data['minutes']} minutes per workout

    LIMITATIONS & CONSIDERATIONS:
    - Allergies/Injuries: {user_data['issues'] if user_data['issues'] else 'None specified'}
    - Food Dislikes: {user_data['dislikes'] if user_data['dislikes'] else 'None specified'}
    - Medical Conditions: {user_data['medical'] if user_data['medical'] else 'None specified'}

    Please provide a detailed plan that includes:

    1. COMPLETE 7-DAY WORKOUT PLAN:
       - MANDATORY: Provide a full week (7 days) of workouts with specific training for each day
       - CRITICAL: Design all workouts based on the preferred training environment ({environment})
         * If "Gym": Include gym equipment (barbells, dumbbells, machines, cables, etc.)
         * If "Home": Focus on bodyweight, resistance bands, and minimal equipment exercises
         * If "Both": Provide alternatives for both gym and home settings
       - ESSENTIAL: Tailor the entire program to match the specified training style preferences ({training_styles})
         * If "Bodybuilder (hypertrophy)": Focus on muscle isolation, higher volume, moderate weights, shorter rest
         * If "Powerlifter (strength)": Emphasize compound movements, heavy weights, lower reps, longer rest
         * If "CrossFit / functional fitness": Include varied movements, circuits, metabolic conditioning
         * If "Science-based / periodized": Use evidence-based programming with planned progression
         * If "Calisthenics / street workout": Focus on bodyweight progressions and skill development
         * If "Endurance / hybrid": Combine strength training with cardiovascular conditioning
         * If multiple styles selected: Blend approaches intelligently throughout the week
       - For each workout day, include:
         * Complete exercise list with EXACT sets, reps, and rest periods (e.g., "3 sets x 8-10 reps, 90 seconds rest")
         * Specific weight/intensity recommendations when applicable
         * Exercise alternatives based on environment preference
         * Training style-specific techniques and methods
         * Detailed warm-up routine (5-10 minutes) tailored to the workout style
         * Cool-down and stretching routine (5-10 minutes)
       - For rest days, include active recovery activities that complement the training style
       - Weekly training split with specific muscle groups/focus for each day aligned with chosen style
       - Progression guidelines over 4-8 weeks specific to the training methodology
       - Exercise form cues and safety tips for each movement, emphasizing style-specific techniques

    2. COMPLETE 7-DAY NUTRITION PLAN:
       - MANDATORY: Provide a full week (7 days) of clean eating meal plans
       - For each day, include:
         * Breakfast with exact foods and portions to hit macro targets
         * Mid-morning snack (if needed)
         * Lunch with exact foods and portions
         * Afternoon snack (if needed)
         * Dinner with exact foods and portions
         * Evening snack (if needed for goals)
         * Pre/post workout nutrition for training days
       - Each meal should specify:
         * Exact food items and quantities
         * Approximate calories and macros (protein/carbs/fats)
         * Preparation method when relevant
       - Meal timing strategy aligned with workout schedule
       - Hydration guidelines throughout each day
       - Supplement recommendations with timing
       - Meal prep tips and grocery list suggestions
       - Clean eating focus with whole, unprocessed foods

    3. COMPREHENSIVE PROGRESSION SYSTEM:
       - MANDATORY: Provide detailed 4-week progression plan with specific weekly adjustments
       - Week 1-2: Foundation phase with exact rep/weight increases
       - Week 3-4: Intensification phase with advanced techniques
       - Progressive overload strategies (weight, reps, sets, tempo, rest periods)
       - Deload week planning and implementation
       - How to transition to intermediate/advanced programming
       - Plateau-breaking techniques and troubleshooting
       - Performance benchmarks and testing protocols
       - Auto-regulation methods for adjusting intensity based on daily readiness

    4. COMPLETE LIFESTYLE OPTIMIZATION:
       - MANDATORY: Comprehensive lifestyle integration covering all aspects of health
       - Sleep optimization: 
         * Ideal sleep duration and timing for recovery
         * Sleep hygiene protocols and bedroom environment setup
         * Pre-sleep routines and supplement timing
         * How to optimize sleep for workout recovery
       - Stress management mastery:
         * Daily stress reduction techniques (breathing, meditation, journaling)
         * Workout stress vs life stress management
         * Cortisol optimization strategies
         * Time management for consistent training
       - Recovery protocols:
         * Active recovery activities for rest days
         * Post-workout recovery routines
         * Weekly recovery assessments
         * Mobility and flexibility programming
       - Social and environmental factors:
         * How to maintain consistency during travel
         * Social eating and training strategies
         * Creating supportive environments
         * Meal prep and planning systems
       - Energy and productivity optimization:
         * Pre-workout nutrition timing and choices
         * Post-workout recovery nutrition
         * Daily energy management around training
         * Supplement timing for performance and recovery

    5. PSYCHOLOGICAL MASTERY & MINDSET:
       - MANDATORY: Comprehensive psychological framework for long-term success
       - Motivation and habit formation:
         * Science-based habit stacking techniques
         * Intrinsic vs extrinsic motivation strategies
         * Building identity-based habits ("I am someone who...")
         * Overcoming motivation dips and maintaining consistency
       - Goal setting and achievement psychology:
         * SMART goal framework with fitness-specific applications
         * Process goals vs outcome goals
         * Celebrating small wins and milestone rewards
         * Vision boarding and long-term goal visualization
       - Mental resilience and confidence building:
         * Overcoming gym intimidation and social anxiety
         * Building body confidence throughout the transformation
         * Dealing with plateaus and temporary setbacks
         * Positive self-talk and internal dialogue management
       - Behavioral psychology applications:
         * Understanding your personal triggers and patterns
         * Environmental design for automatic healthy choices
         * Social accountability and support system building
         * Cognitive reframing for challenges and obstacles
       - Performance psychology:
         * Pre-workout mental preparation routines
         * Mind-muscle connection techniques
         * Visualization for better form and performance
         * Managing perfectionism and all-or-nothing thinking

    6. SAFETY & MODIFICATIONS:
       - Exercise modifications for any mentioned limitations
       - Warning signs to watch for
       - When to rest or deload
       - Injury prevention strategies
       - Form cues and safety protocols

    CRITICAL REQUIREMENTS:
    - You MUST provide a complete 7-day workout schedule with every single exercise, set, rep, and rest period specified
    - You MUST tailor the entire workout program to match the specified training style preferences ({training_styles})
    - You MUST provide a complete 7-day meal plan with every meal and snack detailed with exact foods and portions
    - You MUST include a detailed 4-week progression plan with specific weekly adjustments and techniques
    - You MUST provide comprehensive lifestyle optimization covering sleep, stress, recovery, and social factors
    - You MUST include an extensive psychological mastery section with motivation, mindset, and behavioral strategies
    - The training style preferences are PARAMOUNT - every workout should reflect the chosen methodology
    - Use the calculated nutrition targets as the foundation for all nutrition recommendations
    - Format the response with clear headers, bullet points, and practical actionable advice
    - Ensure the meal plans hit the daily calorie and macro targets within 5-10% accuracy
    - Make every section comprehensive and actionable - this should be a complete transformation guide
    - Include specific techniques, protocols, and step-by-step instructions for maximum value
    """
    
    return prompt

def generate_workout_plan(user_data: Dict[str, Any], api_key: str) -> str:
    """Generate workout plan using OpenAI API."""
    try:
        # Validate API key before using
        if not api_key:
            return "❌ No API key provided to generation function"
        
        if len(api_key) < 50:  # Basic length check
            return f"❌ API key too short: {len(api_key)} characters (expected ~164)"
        
        # Create OpenAI client with the provided API key
        openai_client = OpenAI(api_key=api_key.strip())  # Strip any whitespace
        
        prompt = create_workout_prompt(user_data)
        
        # Create a placeholder for streaming content
        response_placeholder = st.empty()
        full_response = ""
        
        # Stream the response for faster user experience
        stream = openai_client.chat.completions.create(
            model="o3-mini-2025-01-31",  # Using o3-mini for faster streaming completions
            messages=[
                {
                    "role": "system", 
                    "content": "You are an elite fitness and transformation coach with expertise in exercise science, nutrition, psychology, and behavioral change. You combine the knowledge of a certified personal trainer, sports nutritionist, sports psychologist, and lifestyle coach. Your goal is to create comprehensive, life-changing transformation guides that address every aspect of health and fitness. Always prioritize safety, evidence-based practices, and long-term sustainability while delivering maximum value and actionable insights."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            max_completion_tokens=10000,
            temperature=1,
            stream=True
        )
        
        # Stream the response in real-time
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                full_response += chunk.choices[0].delta.content
                response_placeholder.markdown(full_response + "▌")  # Show cursor while typing
        
        # Remove cursor and show final response
        response_placeholder.markdown(full_response)
        return full_response
        
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
st.title("⚡️ FitKit")
st.markdown("""
**— your personal AI training blueprint.**

Drop your info, grab a plan, keep it forever. Simple.

⸻

**What it does:**
- 🧠 Reads your stats and builds workouts + meals around you
- 🔄 Updates as you progress—no more guess-work
- ⏱ Cuts planning time to zero so you can focus on the grind
- 💾 One download = lifetime access

⸻

**Why tap in:**
- Routines tailored for your goals, not a one-size list
- Nutrition guidance that matches the plan
- No subscriptions, no bloated apps—just your kit, on demand

**Hit the quick quiz, claim your FitKit, and get moving.**
""")

# Free access for testing - no paywall
st.success("🚀 **FitKit is now FREE for testing!** Generate your personalized fitness plan below.")

# Get the API key using centralized function
current_api_key, api_key_source = get_api_key()

unit = st.radio("Units", ["Imperial", "Metric"], horizontal=True)

with st.form("intake"):
    email = st.text_input("Email (We won't share or sell your data)")
    age   = st.number_input("Age", 13, 80, step=1)

    sex   = st.radio("Sex", ["Male", "Female", "Other"], horizontal=True)

    if unit == "Imperial":
        col1, col2 = st.columns(2)
        with col1:
            feet = st.number_input("Height (feet)", min_value=3, max_value=8, value=5, step=1)
        with col2:
            inches = st.number_input("Height (inches)", min_value=0, max_value=11, value=8, step=1)
        height = feet * 12 + inches  # Convert to total inches
        weight = st.number_input("Weight (lbs)", min_value=50, max_value=500, value=150, step=1)
    else:
        height = st.number_input("Height (cm)", min_value=120, max_value=250, value=170, step=1)
        weight = st.number_input("Weight (kg)", min_value=30, max_value=200, value=70, step=1)

    goal     = st.selectbox("Primary goal", ["Lose fat", "Build muscle", "Re-comp", "General health"])
    level    = st.radio("Training experience", ["Beginner", "Intermediate", "Advanced"], horizontal=True)
    activity = st.radio("Activity level", ["Sedentary", "Lightly active", "Moderately active", "Very active"], horizontal=True)
    days     = st.slider("Training days per week", 2, 7, 4)
    minutes  = st.slider("Time per workout (minutes)", 20, 90, 45)
    environment = st.radio("Preferred training environment", ["Gym", "Home", "Both"], horizontal=True)
    style    = st.multiselect(
        "Training style preferences",
        ["Bodybuilder (hypertrophy)", "Powerlifter (strength)",
         "CrossFit / functional fitness", "Science-based / periodized",
         "Calisthenics / street workout", "Endurance / hybrid", "Other"]
    )
    diet     = st.selectbox("Diet style", ["Omnivore", "Vegetarian", "Vegan", "Keto", "None"])
    issues   = st.text_area("Allergies / injuries (optional)")
    dislikes = st.text_input("Food dislikes (optional)")
    medical  = st.text_area("Medical conditions / medications (optional)")
    
    # Disclaimer box
    st.markdown("---")
    st.markdown("""
    **⚠️ Important Disclaimer:**
    
    • **Results not guaranteed** - Individual results may vary based on adherence, genetics, and lifestyle factors
    • **For educational purposes only** - This is not medical advice or professional training guidance
    • **Consult professionals** - Always consult with a healthcare provider before starting any new exercise or nutrition program
    • **Use at your own risk** - You assume full responsibility for your health and safety
    • **Fair use policy** - This tool is for personal use only, not for commercial redistribution
    
    By proceeding, you acknowledge you've read and agree to these terms.
    """)

    submitted = st.form_submit_button("Generate my plan")

# Handle form submission
if submitted:
    # Validate required fields
    if not email or not age or not height or not weight:
        st.error("Please fill in all required fields (Email, Age, Height, Weight)")
    elif not validate_email(email):
        st.error("Please enter a valid email address (e.g., user@example.com)")
    elif not current_api_key:
        st.error("🔑 **OpenAI API Key Required!** Please set your API key in Streamlit Cloud secrets. Go to your app settings → Secrets tab → Add: `OPENAI_API_KEY = \"your-api-key-here\"`")
    else:
        # Prepare user data
        user_data = {
            'email': email,
            'age': age,
            'sex': sex,
            'height': height,
            'weight': weight,
            'unit': unit,
            'goal': goal,
            'level': level,
            'days': days,
            'environment': environment,
            'diet': diet,
            'issues': issues,
            'activity': activity,
            'minutes': minutes,
            'style': style,
            'dislikes': dislikes,
            'medical': medical
        }
        
        # Show loading message for streaming
        st.info("🤖 **AI is creating your personalized workout plan...** (streaming live)")
        
        # Get fresh API key for generation
        generation_api_key, generation_source = get_api_key()
        
        workout_plan = generate_workout_plan(user_data, generation_api_key)
        
        # Display success message after streaming is complete
        if workout_plan and not workout_plan.startswith("❌") and not workout_plan.startswith("Error"):
            st.success("🎉 Your personalized FitKit is ready!")
        
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
                file_name=f"{email.replace('@', '_').replace('.', '_')}_complete_fitness_plan.txt",
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
                st.write(f"**Training Environment:** {environment}")
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
