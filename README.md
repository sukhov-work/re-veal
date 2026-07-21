# Reveal

Reveal takes two photos of the same thing at different times, a before and
an after, and lines them up so you can slide between them. Think of a
utility box before and after you painted it: Reveal makes the two photos
sit exactly on top of each other, so the slide feels like the paint appears
on the box, not like the camera jumped.

It gives you three things:

1. A slider in your browser to play with.
2. The two photos, lined up and cropped to match, saved as files.
3. A short video of the reveal, ready to post (Instagram sizes included).

Everything happens on this computer. The photos never go anywhere.

## One-time setup

Open Terminal, go to this folder, and run:

    ./setup.sh

Wait for "Setup finished". That's it.

## Using it

    ./run.sh

Your browser opens with two boxes. Drop the earlier photo on the left,
the later one on the right, and click **Line them up**. Ten seconds or so
later you'll see the slider.

Below the two boxes there is a choice of how alike the photos are:

- **Same scene, re-shot** is the normal one: the same place photographed
  again, from roughly the same spot.
- **Just similar** is for photos that only resemble each other: a
  different person standing in the same place, or two look-alike objects
  photographed in different places. Reveal matches what it can and gives
  you wider hand sliders to finish the job. If a pair fails in the normal
  mode, the error screen offers a one-click retry with this mode.

Drag the line left and right. The left side of the line shows the after,
the right side shows the before.

Under the picture there is a **match score**. Above about 75 means the
photos locked together well. If something looks slightly off, open
**Fine-tune by hand** and nudge it: sideways, up/down, rotate, size, lean,
and how strongly to match the light between the two days. Changes apply
when you let go of a slider. Double-click any slider to reset it.

When it looks right, pick a video shape and length in **Save the result**
and click **Save video** (or **Save aligned photos** for just the two
pictures). The files land in your Downloads.

Click **Start over with two new photos** to do another pair.

To stop Reveal, go back to Terminal and press Ctrl+C.

## What photos work

- JPEG, PNG, HEIC (iPhone), DNG and ARW (Sony raw) all work.
- Shoot the after photo from roughly the same spot as the before photo.
  It doesn't need to be exact: a step to the side, a slight tilt, a
  different zoom, and different weather are all fine.
- If Reveal says the photos don't line up, they were probably taken from
  too different a position, or they don't show enough of the same scene.
  Try the **Just similar** mode, or a pair where more of the background
  matches.

## If Reveal can't line up a difficult pair

Some photos are hard: a blank wall, a repeating pattern, or a big change in
light between the two days. There is an optional extra brain you can install
once that handles those:

    ./setup.sh --learned

It is a large download (about 2 GB) and it makes hard pairs slower, but it
rescues pairs that otherwise fail. Most pairs never need it.

Setup downloads everything it will ever need, once, and checks that it
works. After that it never touches the internet again: the model files sit
in the `models` folder next to Reveal, so you can use it on a plane. If you
move Reveal to another computer, copy the `models` folder along with it and
it will keep working offline.

## If something goes wrong

Run the self-test:

    source .venv/bin/activate && python reveal.py check

Every line should say OK. If one doesn't, run ./setup.sh again.
