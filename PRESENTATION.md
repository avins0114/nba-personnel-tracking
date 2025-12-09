# NBA Player Spacing Analysis - 5 Minute Presentation Script

## Part A: Problem Statement [1 minute]

"In basketball, player spacing refers to how well offensive players spread out across the court. Good spacing creates driving lanes, open shots, and makes defenses work harder. Poor spacing allows defenders to collapse and guard multiple players easily.

The problem is that spacing has traditionally been evaluated subjectively through film study. Coaches and analysts make judgments based on watching possessions, but there's no quantitative way to measure whether spacing is actually good or bad, or to compare spacing across different teams, lineups, or possessions.

This project solves that by building a tool that takes NBA player tracking data and calculates objective spacing metrics - things like floor area coverage, average distances between players, and defensive pressure. It then visualizes these metrics in real-time as you watch plays unfold."

---

## Part B: Why This Matters [1 minute]

"There are three main reasons why quantifying spacing is important.

First, for offensive efficiency analysis. Teams with better spacing generally score more efficiently. Being able to measure this objectively lets you correlate spacing metrics with points scored, effective field goal percentage, and other outcomes.

Second, for player evaluation. Some players create value not just by scoring themselves, but by drawing defensive attention and creating space for teammates. This is often called 'gravity.' With spacing metrics, you can quantify how much space a player like Steph Curry creates just by being on the court.

Third, for strategic decision-making. Should you run five-out sets? How does spacing change throughout a possession? Which lineup combinations create the most space? Having metrics lets you answer these questions with data rather than gut feeling.

NBA teams already do this kind of analysis with their analytics departments. This tool makes that kind of analysis accessible for researchers, students, and basketball enthusiasts."

---

## Part C: Technical Approach [1 minute]

"The tool uses SportVU tracking data, which is the NBA's official player tracking system. It records x-y coordinates for all 10 players plus the ball at 25 frames per second with sub-foot accuracy. The data comes in JSON format with events representing possessions and moments representing individual frames.

For each frame, I calculate several metrics. The convex hull area - essentially drawing a polygon around the five offensive players and measuring how much court area they cover. Average pairwise distance - the mean distance between all pairs of offensive players. And defensive pressure metrics like how close the nearest defender is to each offensive player.

The tool has three main components. First, a data loader that parses the JSON files and handles compressed formats like zip and 7z. Second, a metrics calculator that implements the geometric algorithms using scipy for convex hulls and numpy for distance calculations. Third, a visualizer built with matplotlib that shows animated playback with metrics overlaid on the court.

I also implemented an experimental computer vision mode using YOLOv8 for player detection and DeepSORT for tracking. The idea was to extract player positions directly from broadcast video instead of relying on official tracking data. This mode uses OpenCV for homography to transform pixel coordinates to court coordinates. However, it didn't work very well due to challenges with tracking ID switches, occlusions, and the half-court camera angles typical of broadcasts. I'll discuss that more in the learnings section."

---

## Part D: Demo and Results [1 minute]

**[Screen share terminal, launch `./nba`]**

"Let me show you the tool. You run it with `./nba` which brings up an interactive menu.

**[Select option 1 - View SportVU data]**

I'll select option 1 to view SportVU data. It shows available game files.

**[Select a game file and event number]**

Selecting a game and an event number - let's try event 10 with spacing enabled.

**[Show the visualization]**

Here's the visualization. You can see the court with all 10 players represented as colored dots. The green shaded area is the convex hull of the offensive team - it shows how much floor space they're covering. As the play progresses, watch how this area changes. When players spread out, it expands. When they collapse toward the basket, it shrinks.

The spacing score in the corner updates in real-time on a 0-100 scale. Higher is better spacing.

**[Let it run for a few seconds]**

Now let me show the export functionality.

**[Close window, return to menu, select option 4]**

Option 4 exports all metrics to CSV. You select a game file and it processes all possessions, calculating average spacing scores, hull areas, and defender distances for each event.

**[Show the command running or resulting CSV briefly]**

This lets you do bulk analysis - correlate spacing with outcomes, compare different teams, or study trends over time."

---

## Part E: Learnings and Future Work [1 minute]

"I learned several things from this project.

On the technical side, I gained experience working with large JSON datasets - some of these game files are over 100MB. I also implemented geometric algorithms like convex hull calculation and learned how to build real-time animations with matplotlib's FuncAnimation.

For basketball analytics, the main insight is that spacing is quantifiable. You can objectively measure what 'good spacing' means. The convex hull areas for well-spaced offenses typically range from 600-800 square feet, while cramped possessions might only cover 300-400.

The computer vision experiment taught me important lessons about the limits of CV for this application. The main issues were tracking ID switches when players crossed paths, coordinate transformation errors from the homography mapping, and difficulty detecting small objects - players are only 20-30 pixels in broadcast footage. I tried adding manual player selection to bootstrap the tracker, but ultimately the CV approach achieved maybe 60-70% accuracy compared to ground truth. The lesson is that sometimes using high-quality data sources is better than trying to extract from imperfect sources.

For future work, there are several directions. You could build predictive models using spacing metrics to forecast shot success. You could quantify individual player gravity by measuring how defenders react to different players. You could compare spacing across different NBA eras to study how the game has evolved. Or you could integrate this with shot outcome data to find optimal spacing thresholds for different play types.

The code is open source and documented, so others can build on this work."

---

## Preparation Notes

**Before presentation:**
- Have `./nba` ready to launch
- Pre-select an interesting game/event (event 10-50 usually has action)
- Test that visualizations work
- Optional: Pre-generate a CSV export to show the output format

**During presentation:**
- Keep terminal visible
- Narrate what you're doing during live demo
- Part D should be mostly visual with brief narration

**Timing:**
- Each part: 60 seconds
- Total: 5 minutes
