# Generating the 5-Turn Visual Demo GIF

This guide explains how to capture a short (≈5 decision steps) animation of the Turn Mode visual demo for the README.

## Target Output
- Preferred Repo Location: `images/visualdemo-snakonomicus.gif` (README embed references this)
- Dimensions: 640x480 (match main window) or cropped to focus 320x240 surface
- Duration: ~6–8 seconds (includes initial idle + 5 autoplay steps)
- Size: < 1.2 MB (optimize for repo footprint)

## Capture Steps
1. Activate environment:
   ```bash
   source vmt-dev/bin/activate
   ```
2. Launch the demo with deterministic seed & small step count:
   ```bash
   python scripts/demo_single_agent.py --gui --turn-mode --steps 5 --seed 1234 --density 0.20 --fade-ms 500
   ```
   (Autoplay will advance 1 step per second.)
3. Use a screen recorder (suggested tools):
   - Linux: `peek`, `simplescreenrecorder`, or `ffmpeg`
   - macOS: QuickTime + convert (not ideal) or `ffmpeg` directly
4. If using ffmpeg directly (X11 example, adjust display/window ID):
   ```bash
   # Find window ID (optional) using xwininfo, then:
   ffmpeg -y -video_size 640x480 -framerate 30 -f x11grab -i $DISPLAY -t 7 raw_capture.mp4
   ```
5. Trim (if needed) and export optimized GIF:
   ```bash
   ffmpeg -i raw_capture.mp4 -vf "fps=10,scale=640:-1:flags=lanczos" -loop 0 temp.gif
   gifsicle -O3 --colors 128 temp.gif > images/visualdemo-snakonomicus.gif
   rm temp.gif
   ```
6. Validate determinism note: The visual content should match future runs with same seed & density.
7. Commit the GIF (ensure path matches README):
   ```bash
   git add images/visualdemo-snakonomicus.gif
   git commit -m "docs: add 5-turn visual demo GIF"
   ```

## Optimization Tips
- Lower fps (8–12) sufficient; higher increases size.
- Reduce fade duration or tail length temporarily if size near cap.
- Use `--no-overlay` for a variant if text clarity is low at reduced colors.

## Refresh Procedure
If visualization changes (new overlays or color scheme), regenerate using same seed & command to keep continuity.

-- END --
