import streamlit as st
import pandas as pd
import random
from io import StringIO

# --- Configuration and Constants ---
POINTS_PER_PUMP = 5
TOTAL_TRIALS = 7

# New constants for the increasing risk model:
# The values below represent the *max* number of pumps a balloon can hold.
MAX_PUMPS_MAP = {
    'Yellow': 8,    # High Risk -> Max 8 pumps (original probability 1/8)
    'Orange': 16,   # Moderate Risk -> Max 16 pumps (original probability 1/16)
    'Blue': 64      # Low Risk -> Max 64 pumps (original probability 1/64)
}

DEPARTMENTS = [
    'Select Department',
    'Accounting', 
    'Finance (BAF)', 
    'Management Studies (MGT)', 
    'Entrepreneurship',
    'Marketing',
    'Economics',
    'Other'
]

# --- Session State Initialization ---
if 'page' not in st.session_state:
    st.session_state['page'] = 'start'
if 'trial_data' not in st.session_state:
    st.session_state['trial_data'] = []
if 'total_score' not in st.session_state:
    st.session_state['total_score'] = 0
if 'current_trial' not in st.session_state:
    st.session_state['current_trial'] = 1
if 'temp_score' not in st.session_state:
    st.session_state['temp_score'] = 0
if 'pumps' not in st.session_state:
    st.session_state['pumps'] = 0
if 'balloon_colors_sequence' not in st.session_state:
    # Initialize the randomized sequence of colors for 7 trials
    colors = list(MAX_PUMPS_MAP.keys())
    sequence = random.choices(colors, k=TOTAL_TRIALS)
    st.session_state['balloon_colors_sequence'] = sequence
if 'max_pumps_this_trial' not in st.session_state: # Renamed from 'max_pumps'
    st.session_state['max_pumps_this_trial'] = 0

# --- Helper Functions ---

def setup_new_trial():
    """Sets the max pumps for the current trial based on color sequence."""
    if st.session_state['current_trial'] <= TOTAL_TRIALS:
        current_color = st.session_state['balloon_colors_sequence'][st.session_state['current_trial'] - 1]
        st.session_state['max_pumps_this_trial'] = MAX_PUMPS_MAP[current_color]
        # In a real BART, max_pumps can sometimes be randomized (e.g., from 1 to 128) 
        # but here we use the fixed values corresponding to the risk levels.

def next_trial():
    """Records the outcome and prepares state for the next balloon/trial."""
    current_color = st.session_state['balloon_colors_sequence'][st.session_state['current_trial'] - 1]
    
    # 1. Record data for the finished trial
    # Check explosion state based on how we left the game_page/explosion_page
    is_exploded = 0
    if st.session_state['page'] == 'explosion':
        is_exploded = 1
    elif st.session_state['page'] == 'game_over_explosion':
        is_exploded = 1

    st.session_state['trial_data'].append({
        'participant_name': st.session_state['participant_name'],
        'department': st.session_state['department'],
        'game_id': st.session_state['game_id'],
        'trial_number': st.session_state['current_trial'],
        'balloon_color': current_color,
        'pumps': st.session_state['pumps'],
        'exploded': is_exploded, 
        'money_earned': st.session_state['temp_score'] if is_exploded == 0 else 0, # 0 if exploded
        'total_money_after_trial': st.session_state['total_score']
    })
    
    # 2. Increment trial counter
    st.session_state['current_trial'] += 1
    
    # 3. Reset temporary variables
    st.session_state['temp_score'] = 0
    st.session_state['pumps'] = 0
    
    # 4. Check if game is over
    if st.session_state['current_trial'] > TOTAL_TRIALS:
        st.session_state['page'] = 'end'
    else:
        # 5. Setup for the new trial
        setup_new_trial()
        st.session_state['page'] = 'game'

def handle_pump():
    """Handles the 'Pump' button click and explosion check."""
    
    # Ensure setup is run if not already done (e.g., first pump of a new trial)
    if st.session_state['max_pumps_this_trial'] == 0:
        setup_new_trial()

    max_pumps = st.session_state['max_pumps_this_trial']
    
    st.session_state['pumps'] += 1
    current_pumps = st.session_state['pumps']
    
    st.session_state['temp_score'] += POINTS_PER_PUMP
    
    # --- New Increasing Risk Logic ---
    
    # If maximum pumps are reached, it explodes instantly
    if current_pumps >= max_pumps:
        st.session_state['page'] = 'explosion'
    else:
        # The probability of explosion increases with each pump: 
        # probability = 1 / (Maximum Pumps - Current Pumps + 1)
        # The '+ 1' ensures the denominator starts higher than 0 when current_pumps = max_pumps - 1
        # Example: if max=8, pump=1, prob = 1/(8-1) = 1/7
        # Example: if max=8, pump=7, prob = 1/(8-7) = 1/1
        
        # We will use the formula 1 / (Max_Pumps - Current_Pumps + 1) for a slightly smoother curve
        # and ensure a pop at exactly Max_Pumps
        prob_explosion = 1 / (max_pumps - current_pumps + 1)
        
        # Check for explosion based on this increasing random chance
        if random.random() < prob_explosion:
            st.session_state['page'] = 'explosion'
    
    # Simple growth effect to reflect pumping
    st.session_state['balloon_size'] = 150 + st.session_state['pumps'] * 5

def handle_collect():
    """Handles the 'Collect' button click and saves the temporary score."""
    # Add temporary score to total score
    st.session_state['total_score'] += st.session_state['temp_score']
    # Record data and move to next trial
    next_trial()

def reset_game():
    """Resets the entire session state for a new participant."""
    # Clear all state variables
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    # Rerun the app to reinitialize state
    st.rerun() # Replaced st.experimental_rerun()

# --- UI Components ---

def balloon_ui(color, pumps):
    """Displays the balloon graphic with color and size based on pumps."""
    # Use HTML/CSS to create a colored circle that grows
    size = 150 + pumps * 5
    # Ensure size doesn't get too ridiculous
    size = min(size, 350)
    
    html_content = f"""
    <div style="
        display: flex; 
        flex-direction: column; 
        align-items: center; 
        margin: 20px 0;
    ">
        <div style="
            width: {size}px; 
            height: {size}px; 
            background-color: {color.lower()};
            border-radius: 50%; 
            border: 8px solid #333;
            box-shadow: 0 10px 20px rgba(0,0,0,0.5);
            transition: all 0.1s ease-out;
            display: flex;
            justify-content: center;
            align-items: center;
            color: white;
            font-size: 20px;
            font-weight: bold;
        ">
            PUMPS: {pumps}
        </div>
        <div style="
            width: 5px; 
            height: 50px; 
            background-color: #333;
        "></div>
    </div>
    """
    st.markdown(html_content, unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center;'>Balloon Color: {color}</h3>", unsafe_allow_html=True)

def score_panel_ui():
    """Displays the current scores and trial information."""
    
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Total Earnings", value=f"${st.session_state['total_score']}")
    with col2:
        st.metric(label=f"Trial {st.session_state['current_trial']} of {TOTAL_TRIALS}", value=f"Temporary Score: ${st.session_state['temp_score']}")
    with col3:
        st.metric(label="Pumps This Trial", value=f"{st.session_state['pumps']}")
    st.markdown("---")


# --- Page Functions ---

def start_page():
    """Screen 1: Participant Information Entry."""
    st.title("🎈 Behavioral Risk-Taking Experiment (BART)")
    st.header("1. Participant Information")
    st.markdown("Please enter your details to begin the experiment.")

    with st.form("participant_form"):
        # Name (Text field)
        name = st.text_input("Full Name", key='input_name')
        
        # Department (Dropdown - using selectbox)
        department = st.selectbox("Academic Department", DEPARTMENTS, key='input_department')
        
        # Game ID (Text field)
        game_id = st.text_input("Unique Game ID (e.g., BAF_01)", key='input_game_id')
        
        # Validation and Start Button
        submitted = st.form_submit_button("Start Game")

        if submitted:
            if not name or department == 'Select Department' or not game_id:
                st.error("Please fill out all fields completely.")
            else:
                st.session_state['participant_name'] = name
                st.session_state['department'] = department
                # Ensure Game ID is safe for filenames
                st.session_state['game_id'] = game_id.strip().replace(' ', '_') 
                
                # Setup the first trial max pumps
                setup_new_trial()
                
                st.session_state['page'] = 'game'
                st.rerun() # Replaced st.experimental_rerun()

def game_page():
    """Screen 2: The main BART interface."""
    current_color = st.session_state['balloon_colors_sequence'][st.session_state['current_trial'] - 1]

    st.title(f"Trial {st.session_state['current_trial']} of {TOTAL_TRIALS}")
    
    score_panel_ui()
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        balloon_ui(current_color, st.session_state['pumps'])

    with col2:
        st.subheader("Your Decision")
        st.markdown(f"""
        **Current Risk:** The balloon is **{current_color}**. 
        Each pump adds **${POINTS_PER_PUMP}** to your temporary balance, but the risk of explosion **increases** with every pump!
        """)

        # Action Buttons
        st.button(
            "🎈 PUMP (+ $5)", 
            on_click=handle_pump, 
            type="primary",
            use_container_width=True
        )
        st.markdown("")
        st.button(
            f"💰 COLLECT (${st.session_state['temp_score']})", 
            on_click=handle_collect,
            use_container_width=True,
            disabled=(st.session_state['pumps'] == 0) # Can't collect zero score
        )
        
        # Check if an explosion happened immediately after a pump
        if st.session_state['page'] == 'explosion':
            # This triggers the transition to the explosion screen.
            st.session_state['page'] = 'game_over_explosion'
            st.rerun() # Replaced st.experimental_rerun()


def explosion_page():
    """Displayed immediately after an explosion."""
    current_color = st.session_state['balloon_colors_sequence'][st.session_state['current_trial'] - 1]
    
    st.title("💥 BOOM! Balloon Exploded.")
    
    st.error(f"""
    The **{current_color}** balloon has burst after **{st.session_state['pumps']}** pumps.
    You have lost the temporary balance of **${st.session_state['temp_score']}** for this round.
    """)
    
    # Record the explosion outcome (money_earned will be 0) and proceed
    st.button("Continue to Next Trial", on_click=next_trial, type="primary")
    
    score_panel_ui()


def end_page():
    """Screen 3: End of experiment, display results, and CSV download."""
    st.title("✅ Experiment Complete")
    st.success("Thank you for participating!")

    final_score = st.session_state['total_score']
    st.header(f"Final Total Score: ${final_score}")

    st.markdown("---")
    st.subheader("Data Summary")

    # Convert recorded data list to a DataFrame
    df = pd.DataFrame(st.session_state['trial_data'])
    
    # Ensure column order matches requirements
    required_cols = [
        'participant_name', 'department', 'game_id', 
        'trial_number', 'balloon_color', 'pumps', 
        'exploded', 'money_earned', 'total_money_after_trial'
    ]
    
    # Handle cases where columns might be missing (shouldn't happen, but for robustness)
    df = df.reindex(columns=required_cols)
    
    st.dataframe(df, use_container_width=True)

    # Prepare CSV file for download
    csv_filename = f"BART_{st.session_state['game_id']}.csv"
    csv_string = df.to_csv(index=False)
    
    st.download_button(
        label=f"⬇️ Download Data ({csv_filename})",
        data=csv_string,
        file_name=csv_filename,
        mime='text/csv',
        type="primary"
    )
    
    st.markdown("---")
    st.info("The data has been saved locally as a CSV file. The system is ready to reset.")

    # Reset button for a new participant
    st.button("Start New Participant Session", on_click=reset_game)


# --- Main Application Flow ---

def main():
    st.set_page_config(
        page_title="BART Experiment", 
        layout="centered", 
        initial_sidebar_state="collapsed"
    )

    # Determine which page to display
    if st.session_state['page'] == 'start':
        start_page()
    elif st.session_state['page'] == 'game':
        game_page()
    elif st.session_state['page'] == 'explosion':
        explosion_page()
    elif st.session_state['page'] == 'game_over_explosion':
        # This is a critical state to ensure the explosion event is recorded before continuing
        explosion_page() 
    elif st.session_state['page'] == 'end':
        end_page()

if __name__ == "__main__":
    main()
