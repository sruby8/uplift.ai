from shiny import App, ui, render, reactive
import pandas as pd
import matplotlib.pyplot as plt
import io

# Define UI
app_ui = ui.page_fluid(
    ui.h2("Rotational Velocity Analysis"),
    ui.input_file("file", "Upload CSV File", accept=[".csv"]),
    ui.output_plot("velocity_plot")
)

# Define Server Logic
def server(input, output, session):

    @reactive.Calc
    def process_data():
        file_info = input.file()
        if not file_info:
            return None  # No file uploaded yet

        # Read uploaded CSV file
        df = pd.read_csv(file_info[0]["datapath"])

        # Define required columns
        required_cols = [
            "athlete_name", "handedness", "trunk_rotational_velocity_with_respect_to_ground",
            "pelvis_rotational_velocity_with_respect_to_ground", "left_arm_rotational_velocity_with_respect_to_ground",
            "right_arm_rotational_velocity_with_respect_to_ground", "right_knee_extension_velocity",
            "left_knee_extension_velocity", "foot_contact_time", "ball_release_time", "time"
        ]

        # Ensure required columns exist
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return f"Missing required columns: {', '.join(missing_cols)}"

        # Extract athlete name
        athlete_name = df["athlete_name"].iloc[0]

        # Determine pitcher handedness
        pitcher_handedness = df["handedness"].iloc[0].lower()
        pitcherhand = "LHP" if pitcher_handedness == "left" else "RHP"

        # Select appropriate columns based on handedness
        if pitcherhand == "LHP":
            arm_velocity_col = "left_arm_rotational_velocity_with_respect_to_ground"
            lead_leg_velocity_col = "right_knee_extension_velocity"
        else:
            arm_velocity_col = "right_arm_rotational_velocity_with_respect_to_ground"
            lead_leg_velocity_col = "left_knee_extension_velocity"

        # Extract necessary columns
        subset_data = df[["handedness", arm_velocity_col, "time", "trunk_rotational_velocity_with_respect_to_ground",
                          "pelvis_rotational_velocity_with_respect_to_ground", lead_leg_velocity_col,
                          "foot_contact_time", "ball_release_time"]].copy()

        # Rename columns for clarity
        subset_data.columns = ["handedness", "arm_velocity", "time", "trunk_velocity",
                               "pelvis_velocity", "lead_leg_extension_velocity", "foot_contact_time", "ball_release_time"]

        # Multiply velocity values by -1 if LHP
        if pitcherhand == "LHP":
            velocity_columns = ["pelvis_velocity", "trunk_velocity", "arm_velocity", "lead_leg_extension_velocity"]
            subset_data[velocity_columns] *= -1

        # Locate times for markers safely
        foot_contact_time = subset_data.loc[subset_data["foot_contact_time"] == 0.0, "time"]
        foot_contact_time = foot_contact_time.min() if not foot_contact_time.empty else None

        ball_release_time = subset_data.loc[subset_data["ball_release_time"] == 0.0, "time"]
        ball_release_time = ball_release_time.min() if not ball_release_time.empty else None

        return {
            "subset_data": subset_data,
            "athlete_name": athlete_name,
            "pitcherhand": pitcherhand,
            "foot_contact_time": foot_contact_time,
            "ball_release_time": ball_release_time
        }

    @output
    @render.plot
    def velocity_plot():
        processed = process_data()
        if processed is None or isinstance(processed, str):
            return None  # No file uploaded or error

        subset_data = processed["subset_data"]
        athlete_name = processed["athlete_name"]
        pitcherhand = processed["pitcherhand"]
        foot_contact_time = processed["foot_contact_time"]
        ball_release_time = processed["ball_release_time"]

        # Create the chart
        fig, ax = plt.subplots(figsize=(10, 6), facecolor="black")
        ax.set_facecolor("black")

        # Plot rotational velocities
        ax.plot(subset_data["time"], subset_data["pelvis_velocity"], color="blue", label="Pelvis Rotational Velocity")
        ax.plot(subset_data["time"], subset_data["trunk_velocity"], color="red", label="Trunk Rotational Velocity")
        ax.plot(subset_data["time"], subset_data["arm_velocity"], color="green", label="Pitching Arm Rotational Velocity")
        ax.plot(subset_data["time"], subset_data["lead_leg_extension_velocity"], color="white", label="Lead Leg Extension Velocity")

        # Add vertical markers if they exist
        if foot_contact_time is not None:
            ax.axvline(x=foot_contact_time, color="white", linestyle="dotted", label="Foot Contact Time")
        if ball_release_time is not None:
            ax.axvline(x=ball_release_time, color="yellow", linestyle="dotted", label="Ball Release Time")

        # Customizing the chart for night mode
        ax.set_title(f"Rotational Velocities - {pitcherhand} - {athlete_name}", color="white")
        ax.set_xlabel("Capture Time", color="white")
        ax.set_ylabel("Rotational Velocity", color="white")
        ax.tick_params(colors="white")
        ax.legend(facecolor="black", edgecolor="white", labelcolor="white")
        ax.grid(color="gray", linestyle="--", linewidth=0.5)

        return fig

# Run the app
app = App(app_ui, server)
