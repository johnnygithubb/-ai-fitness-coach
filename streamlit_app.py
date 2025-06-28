import streamlit as st
from openai import OpenAI
import os
import re
from typing import Dict, Any
from dotenv import load_dotenv
from mailersend import emails
import requests
import json
import uuid
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

# Initialize client as None - will be created when needed
client = None

# Paywall functions removed - now running in free mode for testing

# At the top after imports, add URL parameter detection
st.set_page_config(page_title="🎯 Goals need Plans", page_icon="🎯", layout="wide")

# Check URL parameters to detect return from Stripe payment
query_params = st.query_params
paid_user = query_params.get("paid") == "true"
session_id = query_params.get("session_id")

# Store payment status in session state
if paid_user:
    st.session_state.payment_completed = True

# Initialize payment status - set to paid by default
if 'payment_completed' not in st.session_state:
    st.session_state.payment_completed = True

# Generate or restore session ID
if 'user_session_id' not in st.session_state:
    if session_id:
        # Returning from Stripe with session ID
        st.session_state.user_session_id = session_id
        # Try to restore user data from storage
        restore_user_session(session_id)
    else:
        # New session - generate unique ID
        st.session_state.user_session_id = str(uuid.uuid4())[:12]

def validate_email(email):
    """Validate email format using regex."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_confirmation_email(user_email, user_data):
    """Send confirmation email using MailerSend."""
    try:
        # Get MailerSend API key from secrets
        api_key = st.secrets.get("MAILERSEND_API_KEY", os.getenv("MAILERSEND_API_KEY"))
        if not api_key:
            return False
        
        # Initialize MailerSend
        mailer = emails.NewEmail(api_key)
        
        # Email content
        subject = "🎉 Your FitKit Plan is Ready!"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #4CAF50; text-align: center;">⚡️ FitKit</h1>
                
                <h2 style="color: #333;">Your Personal Training Blueprint is Ready!</h2>
                
                <p>Hey there!</p>
                
                <p>Your personalized FitKit plan has been successfully generated! Here's what you got:</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #4CAF50;">Your Plan Details:</h3>
                    <ul style="margin-bottom: 0;">
                        <li><strong>Goal:</strong> {user_data.get('goal', 'Not specified')}</li>
                        <li><strong>Training Days:</strong> {user_data.get('days', 'Not specified')} per week</li>
                        <li><strong>Environment:</strong> {user_data.get('environment', 'Not specified')}</li>
                        <li><strong>Experience Level:</strong> {user_data.get('level', 'Not specified')}</li>
                    </ul>
                </div>
                
                <p><strong>What's included in your plan:</strong></p>
                <ul>
                    <li>🏋️ Complete 7-day workout schedule</li>
                    <li>🍎 Personalized nutrition plan</li>
                    <li>📈 4-week progression system</li>
                    <li>🧠 Psychological mastery tips</li>
                    <li>💤 Lifestyle optimization guide</li>
                </ul>
                
                <p>Remember to save your plan from the app - you have lifetime access to your personalized FitKit!</p>
                
                <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0;"><strong>⚠️ Important:</strong> Always consult with a healthcare provider before starting any new exercise or nutrition program.</p>
                </div>
                
                <p>Ready to transform? Let's get moving! 💪</p>
                
                <p style="color: #666; font-size: 14px; margin-top: 30px;">
                    This email was sent because you generated a FitKit plan. We don't share or sell your data.
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        FitKit - Your Personal Training Blueprint is Ready!
        
        Hey there!
        
        Your personalized FitKit plan has been successfully generated!
        
        Your Plan Details:
        - Goal: {user_data.get('goal', 'Not specified')}
        - Training Days: {user_data.get('days', 'Not specified')} per week
        - Environment: {user_data.get('environment', 'Not specified')}
        - Experience Level: {user_data.get('level', 'Not specified')}
        
        What's included:
        - Complete 7-day workout schedule
        - Personalized nutrition plan
        - 4-week progression system
        - Psychological mastery tips
        - Lifestyle optimization guide
        
        Remember to save your plan from the app - you have lifetime access!
        
        Important: Always consult with a healthcare provider before starting any new exercise or nutrition program.
        
        Ready to transform? Let's get moving!
        
        This email was sent because you generated a FitKit plan. We don't share or sell your data.
        """
        
        # Define an empty dict to populate with mail values
        mail_body = {}
        
        # Configure sender
        mail_from = {
            "name": "FITKIT",
            "email": "test-r83ql3pnez0gzw1j@trial-3zxk54v0qjvg7qrn.mlsender.net"
        }
        
        # Configure recipient
        recipients = [
            {
                "name": "FitKit User",
                "email": user_email
            }
        ]
        
        # Configure reply-to
        reply_to = [
            {
                "name": "FITKIT Support",
                "email": "test-r83ql3pnez0gzw1j@trial-3zxk54v0qjvg7qrn.mlsender.net"
            }
        ]
        
        # Set mail properties
        mailer.set_mail_from(mail_from, mail_body)
        mailer.set_mail_to(recipients, mail_body)
        mailer.set_subject(subject, mail_body)
        mailer.set_html_content(html_content, mail_body)
        mailer.set_plaintext_content(text_content, mail_body)
        mailer.set_reply_to(reply_to, mail_body)
        
        # Send email
        response = mailer.send(mail_body)
        
        if response.status_code == 202:
            st.success("📧 Confirmation email sent! Check your inbox.")
            return True
        else:
            return False
            
    except Exception as e:
        return False

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
    - Name: {user_data['name']}
    - Age: {user_data['age']}
    - Sex: {user_data['sex']}
    - Height: {user_data['height']} {'inches' if user_data['unit'] == 'Imperial' else 'cm'}
    - Weight: {user_data['weight']} {'lbs' if user_data['unit'] == 'Imperial' else 'kg'}

    FITNESS GOALS & EXPERIENCE:
    - Primary Goal: {user_data['goal']}
    - Training Experience: {user_data['level']}
    - Training Days per Week: {user_data['days']}
    - Activity Level: {user_data['activity']}
    - Add Cardio: {user_data['add_cardio']}
    - Add Ab Circuit: {user_data['add_abs']}

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
    - Cardio Addition: {user_data['add_cardio']}
    - Ab Circuit Addition: {user_data['add_abs']}

    LIMITATIONS & CONSIDERATIONS:
    - Allergies/Injuries: {user_data['issues'] if user_data['issues'] else 'None specified'}
    - Food Dislikes: {user_data['dislikes'] if user_data['dislikes'] else 'None specified'}
    - Medical Conditions: {user_data['medical'] if user_data['medical'] else 'None specified'}

    CRITICAL: Start your response with a warm, personal welcome greeting that:
    - Addresses {user_data['name']} by name
    - Acknowledges their specific goal of {user_data['goal']}
    - Mentions this plan was created specifically for them
    - Briefly explains what their personalized plan includes
    - Sets an encouraging, motivational tone
    - Transitions smoothly into the detailed plan sections

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
         * Number of exercises should be based on user's experience level ({user_data['level']})
         * Specific weight/intensity recommendations when applicable
         * Exercise alternatives based on environment preference
         * Training style-specific techniques and methods
         * Detailed warm-up routine (5-10 minutes) tailored to the workout style
         * CARDIO INTEGRATION: {"If user selected 'Yes' for cardio, add 10-30 minutes of cardio to each workout day based on their goal (" + user_data['goal'] + "). Fat loss goals get more cardio (20-30 min), muscle building gets less (10-15 min). Include specific cardio exercises and intensity." if user_data['add_cardio'] == 'Yes' else "No additional cardio requested."}
         * AB CIRCUIT INTEGRATION: {"If user selected 'Yes' for ab circuit, add a 5-minute bodyweight ab routine to finish each workout. Include 4-5 ab exercises with specific sets/reps (e.g., planks, crunches, bicycle crunches, leg raises, mountain climbers)." if user_data['add_abs'] == 'Yes' else "No ab circuit requested."}
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

def generate_workout_plan(user_data: Dict[str, Any], api_key: str, streaming_placeholder=None) -> str:
    """Generate workout plan using OpenAI API with optional streaming display."""
    try:
        # Validate API key before using
        if not api_key:
            return "❌ No API key provided to generation function"
        
        if len(api_key) < 50:  # Basic length check
            return f"❌ API key too short: {len(api_key)} characters (expected ~164)"
        
        # Create OpenAI client with the provided API key
        openai_client = OpenAI(api_key=api_key.strip())  # Strip any whitespace
        
        prompt = create_workout_prompt(user_data)
        
        # Initialize response
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
                
                # Update the streaming placeholder if provided
                if streaming_placeholder:
                    streaming_placeholder.markdown(
                        f"""
                        <div style="
                            background-color: #f0f2f6; 
                            padding: 20px; 
                            border-radius: 10px; 
                            border: 1px solid #ddd;
                            height: 400px;
                            overflow-y: auto;
                            font-family: monospace;
                            white-space: pre-wrap;
                        ">
                        <strong>🤖 Your plan is being generated live:</strong><br/><br/>
                        {full_response}▌
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        
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

def store_review_to_jsonbin(review_data):
    """Store review data to JSONBin.io - tries multiple methods"""
    try:
        # Get all credentials from Streamlit secrets
        master_key = st.secrets.get("JSONBIN_MASTER_KEY", os.getenv("JSONBIN_MASTER_KEY"))
        access_key = st.secrets.get("JSONBIN_ACCESS_KEY", os.getenv("JSONBIN_ACCESS_KEY"))
        bin_id = st.secrets.get("JSONBIN_BIN_ID", os.getenv("JSONBIN_BIN_ID"))
        collection_id = st.secrets.get("JSONBIN_COLLECTION_ID", os.getenv("JSONBIN_COLLECTION_ID"))
        
        # Add timestamp and unique ID to review
        review_data['timestamp'] = datetime.now().isoformat()
        review_data['review_id'] = str(uuid.uuid4())[:8]
        
        # Debug info
        st.write(f"🔍 **Debug Info:**")
        st.write(f"- Master Key: {'✅ Found' if master_key else '❌ Missing'}")
        st.write(f"- Access Key: {'✅ Found' if access_key else '❌ Missing'}")
        st.write(f"- Bin ID: {bin_id if bin_id else '❌ Missing'}")
        st.write(f"- Collection ID: {collection_id if collection_id else '❌ Missing'}")
        
        # Method 1: Try creating a new bin in the collection
        if master_key and collection_id:
            st.write("🔄 **Trying Method 1: Create new bin in collection...**")
            
            headers = {
                'Content-Type': 'application/json',
                'X-Master-Key': master_key,
                'X-Collection-Id': collection_id
            }
            
            create_url = 'https://api.jsonbin.io/v3/b'
            create_response = requests.post(create_url, headers=headers, json=review_data)
            
            st.write(f"- Create Response: {create_response.status_code}")
            if create_response.status_code == 200:
                st.success("✅ **Method 1 worked!** Review stored in new bin within collection.")
                return True
            else:
                st.write(f"- Error: {create_response.text}")
        
        # Method 2: Try updating existing bin
        if master_key and bin_id:
            st.write("🔄 **Trying Method 2: Update existing bin...**")
            
            headers = {
                'Content-Type': 'application/json',
                'X-Master-Key': master_key,
                'X-Bin-Meta': 'false'
            }
            
            read_url = f'https://api.jsonbin.io/v3/b/{bin_id}/latest'
            read_response = requests.get(read_url, headers=headers)
            
            if read_response.status_code == 200:
                existing_data = read_response.json().get('record', [])
                if not isinstance(existing_data, list):
                    existing_data = []
            else:
                existing_data = []
            
            existing_data.append(review_data)
            
            update_url = f'https://api.jsonbin.io/v3/b/{bin_id}'
            update_response = requests.put(update_url, headers=headers, json=existing_data)
            
            st.write(f"- Update Response: {update_response.status_code}")
            if update_response.status_code == 200:
                st.success("✅ **Method 2 worked!** Review added to existing bin.")
                return True
            else:
                st.write(f"- Error: {update_response.text}")
        
        st.error("❌ All methods failed. Check your JSONBin setup.")
        return False
        
    except Exception as e:
        st.error(f"❌ Error storing review: {str(e)}")
        return False

def show_review_popup():
    """Show the popup review modal"""
    # Create a popup-like container
    st.markdown("---")
    st.markdown('<div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border: 2px solid #1f77b4;">', unsafe_allow_html=True)
    
    st.markdown("### 💬 Quick Review - Help Us Improve!")
    st.info("📝 **Your feedback matters!** Please share your experience to help us make FitKit better for everyone.")
    
    # Review form
    with st.form("popup_review_form", clear_on_submit=False):
        col1, col2 = st.columns([1, 1])
        
        with col1:
            nickname = st.text_input(
                "👤 Nickname",
                placeholder="e.g. FitGuru, HealthyJoe, etc.",
                help="How should we display your review? (Optional - will show as 'Anonymous' if empty)"
            )
        
        with col2:
            rating = st.select_slider(
                "⭐ Rating",
                options=[1, 2, 3, 4, 5],
                value=5,
                format_func=lambda x: "⭐" * x + f" ({x}/5)"
            )
        
        review_text = st.text_area(
            "💭 Your Review",
            placeholder="What did you think of your FitKit plan? Any suggestions for improvement?",
            help="Share your honest feedback - it helps us improve!",
            height=100
        )
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            submit_review = st.form_submit_button("✅ Submit & Download", type="primary")
        with col2:
            skip_review = st.form_submit_button("⏭️ Skip & Download")
        with col3:
            cancel = st.form_submit_button("❌ Cancel")
        
        if submit_review:
            # Prepare review data
            review_data = {
                'nickname': nickname if nickname.strip() else 'Anonymous',
                'rating': rating,
                'review_text': review_text,
                'user_goal': st.session_state.get('user_goal', ''),
                'user_level': st.session_state.get('user_level', ''),
                'user_environment': st.session_state.get('user_environment', '')
            }
            
            # Store review
            if store_review_to_jsonbin(review_data):
                st.success("🎉 **Thank you for your review!** Your download is ready below.")
                st.balloons()
            else:
                st.error("❌ Failed to submit review. You can still download your plan below.")
            
            st.session_state.review_submitted = True
            st.session_state.show_review_popup = False
            st.rerun()
                
        elif skip_review:
            st.info("⏭️ Review skipped. Your download is ready below.")
            st.session_state.show_review_popup = False
            st.session_state.review_skipped = True
            st.rerun()
            
        elif cancel:
            st.session_state.show_review_popup = False
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def save_user_session(session_id, user_data, workout_plan):
    """Save user session data to JSONBin for restoration after Stripe payment."""
    try:
        # Get JSONBin credentials
        master_key = st.secrets.get("JSONBIN_MASTER_KEY", os.getenv("JSONBIN_MASTER_KEY"))
        if not master_key:
            return False
        
        # Create session data
        session_data = {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'user_data': user_data,
            'workout_plan': workout_plan,
            'nutrition_data': st.session_state.get('nutrition_data', {}),
            'expires_at': (datetime.now() + timedelta(hours=24)).isoformat()  # Expire in 24 hours
        }
        
        # Store in JSONBin
        headers = {
            'Content-Type': 'application/json',
            'X-Master-Key': master_key,
            'X-Bin-Meta': 'false'
        }
        
        create_url = 'https://api.jsonbin.io/v3/b'
        response = requests.post(create_url, headers=headers, json=session_data)
        
        if response.status_code == 200:
            # Store the bin ID for this session
            bin_data = response.json()
            st.session_state.session_bin_id = bin_data.get('metadata', {}).get('id')
            return True
        
        return False
        
    except Exception as e:
        st.error(f"Error saving session: {str(e)}")
        return False

def restore_user_session(session_id):
    """Restore user session data from JSONBin after Stripe return."""
    try:
        st.info(f"🔄 Restoring session {session_id}...")
        
        # Get JSONBin credentials
        master_key = st.secrets.get("JSONBIN_MASTER_KEY", os.getenv("JSONBIN_MASTER_KEY"))
        if not master_key:
            st.error("❌ No JSONBin master key found for session restoration")
            return False
        
        # For simplicity, we'll store the session data in a predictable bin ID
        # In production, you'd have a proper database lookup
        # For now, let's try to restore from session state if it exists
        
        # Check if we have session data stored
        if hasattr(st.session_state, 'session_bin_id') and st.session_state.session_bin_id:
            headers = {
                'Content-Type': 'application/json',
                'X-Master-Key': master_key,
                'X-Bin-Meta': 'false'
            }
            
            read_url = f'https://api.jsonbin.io/v3/b/{st.session_state.session_bin_id}/latest'
            response = requests.get(read_url, headers=headers)
            
            if response.status_code == 200:
                session_data = response.json().get('record', {})
                
                # Restore session state
                if session_data.get('session_id') == session_id:
                    st.session_state.workout_plan = session_data.get('workout_plan', '')
                    st.session_state.nutrition_data = session_data.get('nutrition_data', {})
                    
                    # Restore user data
                    user_data = session_data.get('user_data', {})
                    st.session_state.user_name = user_data.get('name', 'User')
                    st.session_state.user_goal = user_data.get('goal', '')
                    st.session_state.user_level = user_data.get('level', '')
                    st.session_state.user_environment = user_data.get('environment', '')
                    st.session_state.plan_generated = True
                    
                    st.success(f"✅ Session {session_id} restored successfully!")
                    return True
        
        # If no stored session found, show message
        st.warning(f"⚠️ Could not restore session {session_id}. You may need to regenerate your plan.")
        return False
        
    except Exception as e:
        st.error(f"❌ Error restoring session: {str(e)}")
        return False

# Streamlit App Title
st.title("🎯 Goals need Plans")
st.markdown('<h2 style="text-align: center; color: white; margin-bottom: 30px;">FitKit - Your Ultra Personalized Fitness & Nutrition BluePrint</h2>', unsafe_allow_html=True)

st.markdown("""
### 📦 **What's Included**
- 🏋️ **Complete 7-Day Workout Plan** — tailored to your environment & goals
- 🍎 **Personalized Nutrition Guide** — exact meals, portions & timing
- 📈 **4-Week Progression System** — never plateau again

### ⚡ **How It Works**
- 📝 **Answer Quick Questions** — your stats, goals & preferences  
- 🤖 **AI Creates Your Plan** — personalized in under 60 seconds
- 📥 **Download & Keep Forever** — no subscriptions, it's yours

### 🚀 **Why It's Amazing**
- 🎯 **Built For YOU** — not generic cookie-cutter plans
- 🧠 **Science-Based** — proven methods that actually work  
- ⚡ **Zero Planning Time** — go from idea to action instantly

### 🎁 **Bonus Features**
- 🧠 **Psychological Mastery** — mindset, motivation & habit formation strategies
- 📊 **Exact Calories & Macros** — BMR, TDEE & precise nutritional breakdowns  
- 💤 **Lifestyle Optimization** — sleep, stress management & recovery protocols
- 🛡️ **Safety & Modifications** — injury prevention & exercise alternatives
- 📈 **Plateau-Breaking Techniques** — advanced progression & auto-regulation methods

---
""")

# Get the API key using centralized function
current_api_key, api_key_source = get_api_key()

unit = st.radio("Units", ["Imperial", "Metric"], horizontal=True)

with st.form("intake"):
    name = st.text_input("Name")
    age   = st.number_input("Age", min_value=13, max_value=80, step=1, value=None, placeholder="Enter your age")

    sex   = st.radio("Sex", ["Male", "Female", "Other"], horizontal=True)

    if unit == "Imperial":
        col1, col2 = st.columns(2)
        with col1:
            feet = st.number_input("Height (feet)", min_value=3, max_value=8, value=None, step=1, placeholder="e.g. 5")
        with col2:
            inches = st.number_input("Height (inches)", min_value=0, max_value=11, value=None, step=1, placeholder="e.g. 8")
        height = (feet or 0) * 12 + (inches or 0)  # Convert to total inches, handle None values
        weight = st.number_input("Weight (lbs)", min_value=50, max_value=500, value=None, step=1, placeholder="e.g. 150")
    else:
        height = st.number_input("Height (cm)", min_value=120, max_value=250, value=None, step=1, placeholder="e.g. 170")
        weight = st.number_input("Weight (kg)", min_value=30, max_value=200, value=None, step=1, placeholder="e.g. 70")

    goal     = st.selectbox("Primary goal", ["Lose fat", "Build muscle", "Re-comp", "General health"])
    level    = st.radio("Training experience", ["Beginner", "Intermediate", "Advanced"], horizontal=True)
    activity = st.radio("Activity level", ["Sedentary", "Lightly active", "Moderately active", "Very active"], horizontal=True)
    days     = st.slider("Training days per week", 2, 7, 4)
    environment = st.radio("Preferred training environment", ["Gym", "Home", "Both"], horizontal=True)
    style    = st.multiselect(
        "Training style preferences",
        ["Bodybuilder (hypertrophy)", "Powerlifter (strength)",
         "CrossFit / functional fitness", "Science-based / periodized",
         "Calisthenics / street workout", "Endurance / hybrid", "Other"]
    )
    diet     = st.selectbox("Diet style", ["Omnivore", "Vegetarian", "Vegan", "Keto", "None"])
    
    # Cardio option
    add_cardio = st.radio("Add cardio to routine?", ["No", "Yes"], horizontal=True)
    if add_cardio == "Yes":
        st.caption("⚠️ Will add 10-30 minutes of cardio to each workout based on your goal (increases difficulty and fatigue)")
    
    # Abs option  
    add_abs = st.radio("Add ab circuit for 6-pack?", ["No", "Yes"], horizontal=True)
    if add_abs == "Yes":
        st.caption("⚠️ Will add 5-minute bodyweight ab routine to finish each workout (increases difficulty and fatigue)")
    
    issues   = st.text_area("Allergies / injuries (optional)")
    dislikes = st.text_input("Food dislikes (optional)")
    medical  = st.text_area("Medical conditions / medications (optional)")
    
    # Disclaimer checkbox
    st.markdown("---")
    disclaimer_agreed = st.checkbox(
        "⚠️ I understand this is for educational purposes only, not medical advice. I will consult healthcare professionals before starting any new program and use this at my own risk.",
        help="Click to agree to terms and enable plan generation"
    )

    submitted = st.form_submit_button("Generate my plan")

# Handle form submission
if submitted:
    # Validate required fields
    if not name or age is None or height is None or height == 0 or weight is None:
        st.error("Please fill in all required fields (Name, Age, Height, Weight)")
    elif not disclaimer_agreed:
        st.error("⚠️ Please agree to the disclaimer terms to continue")
    elif not current_api_key:
        st.error("🔑 **OpenAI API Key Required!** Please set your API key in Streamlit Cloud secrets. Go to your app settings → Secrets tab → Add: `OPENAI_API_KEY = \"your-api-key-here\"`")
    else:
        # Prepare user data
        user_data = {
            'name': name,
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
            'style': style,
            'dislikes': dislikes,
            'medical': medical,
            'add_cardio': add_cardio,
            'add_abs': add_abs
        }
        
        # Create a large text area to show streaming
        st.markdown("### 🤖 **AI is creating your personalized workout plan...**")
        streaming_container = st.container()
        
        with streaming_container:
            # Create a text area that will show the streaming content
            streaming_placeholder = st.empty()
            
            with streaming_placeholder:
                st.text_area(
                    "Your plan is being generated:",
                    value="🔄 Analyzing your fitness profile...\n🔄 Calculating optimal workout structure...\n🔄 Customizing exercises for your goals...",
                    height=400,
                    disabled=True,
                    key="streaming_preview"
                )
        
        # Get fresh API key for generation
        generation_api_key, generation_source = get_api_key()
        
        # Generate the workout plan
        workout_plan = generate_workout_plan(user_data, generation_api_key, streaming_placeholder)
        
        # Show the complete plan with blur effect for non-paid users
        if workout_plan and not workout_plan.startswith("❌") and not workout_plan.startswith("Error"):
            # Clear the streaming placeholder and show final result
            streaming_placeholder.empty()
            
            # Show complete plan with conditional blur
            if st.session_state.payment_completed:
                # Show unblurred for paid users
                st.markdown(
                    f"""
                    <div style="
                        background-color: #f0f2f6; 
                        padding: 20px; 
                        border-radius: 10px; 
                        border: 1px solid #ddd;
                        height: 400px;
                        overflow-y: auto;
                        font-family: monospace;
                        white-space: pre-wrap;
                    ">
                    <strong>✅ Your complete personalized FitKit plan:</strong><br/><br/>
                    {workout_plan}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                # Show blurred for free users (the devious part!)
                st.markdown(
                    f"""
                    <div style="
                        position: relative;
                        background-color: #f0f2f6; 
                        padding: 20px; 
                        border-radius: 10px; 
                        border: 1px solid #ddd;
                        height: 400px;
                        overflow-y: auto;
                        font-family: monospace;
                        white-space: pre-wrap;
                        filter: blur(3px);
                        pointer-events: none;
                    ">
                    <strong>🔒 Your complete personalized FitKit plan:</strong><br/><br/>
                    {workout_plan}
                    </div>
                    <div style="
                        position: absolute;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        background: rgba(255,255,255,0.95);
                        padding: 20px;
                        border-radius: 10px;
                        text-align: center;
                        border: 2px solid #4CAF50;
                        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
                        z-index: 1000;
                    ">
                        <h3 style="color: #333; margin: 0;">🔒 Plan Ready - Payment Required!</h3>
                        <p style="color: #666; margin: 10px 0;">Your amazing plan is complete but locked</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            # Wait a moment for them to see it, then show the paywall OR download if paid
            st.success("🎉 **Your personalized FitKit is ready!**")
            
            # Check if user has already paid
            if st.session_state.payment_completed:
                # Show unblurred plan and download button for paid users
                st.markdown("---")
                st.success("🎉 **Thank you for your purchase! Your plan is ready to download.**")
                
                # Show download button with review option
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.download_button(
                        label="📥 Download Your Complete FitKit Plan",
                        data=workout_plan,
                        file_name=f"{name.replace(' ', '_')}_complete_fitness_plan.txt",
                        mime="text/plain",
                        type="primary",
                        key="paid_download"
                    )
                with col2:
                    if st.button("💬 Leave a Review", key="review_button"):
                        st.session_state.show_review_popup = True
                        st.rerun()
                
                # Show nutrition data for paid users
                nutrition_data = calculate_target_calories_and_macros(user_data)
                
                # Create tabs for better organization
                tab1, tab2 = st.tabs(["🍎 Nutrition Targets", "📊 Your Profile"])
                
                with tab1:
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
                
                with tab2:
                    st.markdown("### Your Fitness Profile")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Age", f"{age} years")
                        st.metric("Height", f"{height} {'in' if unit == 'Imperial' else 'cm'}")
                        st.metric("Weight", f"{weight} {'lbs' if unit == 'Imperial' else 'kg'}")
                        st.metric("Training Days", f"{days} per week")
                    
                    with col2:
                        st.write(f"**Primary Goal:** {goal}")
                        st.write(f"**Experience Level:** {level}")
                        st.write(f"**Activity Level:** {activity}")
                        st.write(f"**Training Environment:** {environment}")
                        if style:
                            st.write(f"**Training Style:** {', '.join(style)}")
            
            else:
                # THE DEVIOUS PAYWALL - blur the content and demand payment
                st.markdown("---")
            
            # Blur overlay with payment requirement
            base_stripe_link = st.secrets.get("stripe_link", "https://buy.stripe.com/your-payment-link")
            # Add return URL parameter to redirect back with paid=true and session_id
            current_url = "https://fitkit-app.streamlit.app"  # Replace with your actual Streamlit app URL
            session_id = st.session_state.user_session_id
            return_url = f"{current_url}?paid=true&session_id={session_id}"
            # Note: You'll need to configure this return URL in your Stripe payment settings
            stripe_link = base_stripe_link
            
            st.info(f"🔑 **Session ID:** `{session_id}` (for debugging)")
            st.info(f"🔗 **Return URL:** `{return_url}`")
            
            st.markdown(
                f"""
                <div style="
                    position: relative;
                    background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(240,240,240,0.95));
                    padding: 40px;
                    border-radius: 15px;
                    text-align: center;
                    border: 3px solid #4CAF50;
                    margin: 20px 0;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                ">
                    <h2 style="color: #333; margin-bottom: 20px;">🔒 **Unlock Your Complete FitKit Plan**</h2>
                    <p style="font-size: 18px; color: #666; margin-bottom: 30px;">
                        You've seen how personalized and detailed your plan is!<br/>
                        <strong>Get lifetime access to download and keep this plan forever.</strong>
                    </p>
                    
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
                        <h3 style="color: #4CAF50; margin: 0;">✨ What You Get:</h3>
                        <ul style="text-align: left; display: inline-block; margin: 15px 0;">
                            <li>📋 Your complete 7-day workout plan</li>
                            <li>🍎 Personalized nutrition targets & macros</li>
                            <li>📈 4-week progression system</li>
                            <li>🧠 Psychology & mindset strategies</li>
                            <li>💾 Download & keep forever</li>
                        </ul>
                    </div>
                    
                    <div style="margin: 30px 0;">
                        <a href="{stripe_link}" target="_blank" style="
                            background: linear-gradient(135deg, #4CAF50, #45a049);
                            color: white;
                            padding: 20px 40px;
                            text-decoration: none;
                            border-radius: 12px;
                            font-size: 20px;
                            font-weight: bold;
                            display: inline-block;
                            border: none;
                            cursor: pointer;
                            transition: all 0.3s;
                            box-shadow: 0 5px 15px rgba(76, 175, 80, 0.3);
                        ">
                            🚀 Get Your FitKit - Only $9.99
                        </a>
                    </div>
                    
                    <p style="font-size: 14px; color: #888; margin-top: 20px;">
                        💡 One-time payment • Lifetime access • 30-day money-back guarantee<br/>
                        <em>After payment, you'll be redirected back here with full access!</em>
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Store data in session state for after payment
            st.session_state.workout_plan = workout_plan
            st.session_state.user_name = name
            st.session_state.user_goal = goal
            st.session_state.user_level = level
            st.session_state.user_environment = environment
            st.session_state.plan_generated = True
            
            # Calculate nutrition data for display
            nutrition_data = calculate_target_calories_and_macros(user_data)
            st.session_state.nutrition_data = nutrition_data
            
            # Save session data for Stripe return
            session_saved = save_user_session(
                st.session_state.user_session_id, 
                user_data, 
                workout_plan
            )
            if session_saved:
                st.success("💾 Session saved for payment processing")
            else:
                st.warning("⚠️ Could not save session - you may need to regenerate after payment")

# Handle review popup if triggered (for paid users)
if st.session_state.get('show_review_popup', False):
    show_review_popup()

# Add footer
st.markdown("---")
st.markdown("*Disclaimer: This AI-generated workout plan is for informational purposes only. Consult with a healthcare professional before starting any new exercise program.*")
