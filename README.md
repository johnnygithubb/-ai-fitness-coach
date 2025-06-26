# 🏋️ AI Fitness Coach

An intelligent, personalized fitness and nutrition planning app powered by OpenAI GPT-4 and built with Streamlit.

## 🚀 Features

### 🎯 Personalized Fitness Planning
- **Custom Workout Plans** - AI-generated routines based on your goals, experience, and available equipment
- **Scientific Nutrition Calculations** - BMR, TDEE, and macro targets using proven formulas
- **Goal-Specific Programming** - Tailored for fat loss, muscle building, recomposition, or general health

### 📊 Advanced Nutrition Analysis
- **Precise Calorie Targets** - Calculated based on your metabolism and goals
- **Macro Breakdown** - Protein, carbs, and fats in grams and calories
- **Diet-Specific Adjustments** - Support for Keto, Vegan, Vegetarian, and standard diets
- **Visual Charts** - Interactive macro distribution displays

### 🎨 User-Friendly Interface
- **Comprehensive Form** - Detailed intake questionnaire
- **Three-Tab Results** - Complete plan, nutrition targets, and profile overview
- **Download Feature** - Export your complete fitness plan
- **Responsive Design** - Works on desktop and mobile

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Setup
1. **Clone the repository**
   ```bash
   git clone https://github.com/johnnygithubb/ai-fitness-coach.git
   cd ai-fitness-coach
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your OpenAI API key**
   
   **Option A: Environment Variable (Recommended)**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```
   
   **Option B: Create a .env file**
   ```bash
   echo "OPENAI_API_KEY=your-api-key-here" > .env
   ```
   
   **Option C: Use the app's sidebar**
   - Enter your API key directly in the app interface

5. **Run the app**
   ```bash
   streamlit run app.py
   ```

6. **Open your browser**
   - Navigate to `http://localhost:8501`

## 📱 Usage

### 1. Personal Information
- Enter your basic details (name, age, height, weight)
- Select your biological sex and preferred units

### 2. Fitness Goals & Experience
- Choose your primary goal (lose fat, build muscle, recomposition, general health)
- Select your training experience level
- Set training frequency and session duration

### 3. Equipment & Preferences
- Select available equipment
- Choose your preferred training style
- Specify dietary preferences

### 4. Advanced Options (Optional)
- Set activity level
- Specify food dislikes or allergies
- Note any medical conditions or injuries

### 5. Generate Your Plan
- Click "Generate my plan" to create your personalized program
- View results in three organized tabs:
  - **Complete Plan**: AI-generated workout and nutrition guidance
  - **Nutrition Targets**: Detailed calorie and macro breakdowns with charts
  - **Your Profile**: Summary of your information and goals

## 🧮 Nutrition Calculations

### BMR (Basal Metabolic Rate)
Uses the Mifflin-St Jeor equation for accurate metabolic rate calculation:
- **Men**: BMR = 10 × weight(kg) + 6.25 × height(cm) - 5 × age + 5
- **Women**: BMR = 10 × weight(kg) + 6.25 × height(cm) - 5 × age - 161

### TDEE (Total Daily Energy Expenditure)
Adjusts BMR based on activity level and training frequency:
- **Sedentary**: BMR × 1.2
- **Lightly Active**: BMR × 1.375
- **Moderately Active**: BMR × 1.55
- **Very Active**: BMR × 1.725

### Goal-Specific Calorie Adjustments
- **Fat Loss**: -500 calories (1 lb/week loss)
- **Muscle Building**: +300 calories (lean gains)
- **Recomposition**: Maintenance calories
- **General Health**: -100 calories (gradual improvement)

### Macro Distribution
Optimized ratios based on goals and dietary preferences:

| Goal | Protein | Carbs | Fats |
|------|---------|-------|------|
| Fat Loss | 35% | 35% | 30% |
| Muscle Building | 30% | 45% | 25% |
| Recomposition | 25% | 45% | 30% |
| General Health | 25% | 45% | 30% |

**Special Diets:**
- **Keto**: 25% protein, 5% carbs, 70% fats
- **Vegan**: 20% protein, 55% carbs, 25% fats

## 🔧 Technical Details

### Built With
- **[Streamlit](https://streamlit.io/)** - Web app framework
- **[OpenAI GPT-4](https://openai.com/)** - AI-powered plan generation
- **[Python](https://python.org/)** - Core programming language

### Key Dependencies
- `streamlit>=1.28.0` - Web interface
- `openai>=1.0.0` - AI integration
- `python-dotenv>=1.0.0` - Environment variable management

### File Structure
```
ai-fitness-coach/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── README.md          # Project documentation
└── venv/              # Virtual environment (not in repo)
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This AI-generated workout and nutrition plan is for informational purposes only. Always consult with a healthcare professional before starting any new exercise program or making significant dietary changes.

## 🙏 Acknowledgments

- OpenAI for providing the GPT-4 API
- Streamlit team for the amazing web app framework
- The fitness and nutrition science community for evidence-based methodologies

---

**Made with ❤️ and 🤖 by [johnnygithubb](https://github.com/johnnygithubb)** 