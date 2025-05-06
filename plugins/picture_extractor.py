import glob
import shutil
import click
import cv2
import os
import filetype
from scipy import signal
import numpy as np

@click.group(name="PES", help="Picture Extractor Subsystem Control")
def pic():
    ctx = click.get_current_context().obj
    if 'PES' not in ctx:
        ctx['PES'] = {}

@pic.command(name="config")
@click.option('--working', '-w',
              type=click.Path(file_okay=False, resolve_path=True),
              help=("Picture extractor working location. File I/O operations "
                    "will take place in this directory."))
@click.option('--source', '-s',
              type=click.Path(exists=True, file_okay=False, resolve_path=True),
              help="Data source location (e.g. folder on camera SD card).")
@click.option('--dest', '-d',
              type=click.Path(file_okay=False, resolve_path=True),
              help=("Extracted file destination location (if differs from "
                    "working location)."))
def config_default_locations(working=None, source=None, dest=None):
    """Set directories used by the picture extractor.

    The working location is the directory the picture extractor will use for
    file operations. This should either be a new directory which the tool will
    create or an empty directory.

    The source location is likely a location on your camera SD card (unless
    files have already been transfered) and is likely prefixed by D:/ or E:/.

    The destination location allows you to specify where to put the extracted
    images. If no destination is given, the tool will place the extracted
    pictures in the working location.
    """
    ctx = click.get_current_context().obj
    if working:
        if not os.path.exists(working):
            click.echo(f"Creating working directory: {working}")
            os.makedirs(working)
            ctx['PES']['working'] = working
        elif os.path.isdir(working) and not os.listdir(working):
            click.echo(f"Setting working directory to: {working}")
            ctx['PES']['working'] = working
        elif os.path.isdir(working):
            click.echo(f"Selected working directory ({working}) is not empty!")
        else:
            click.echo(f"Unknown issue encountered while setting working "
                       f"directory to: {working}")
    if source:
        if not os.path.exists(source):
            click.echo(f"Selected source directory {source} does not exist!")
        elif os.path.isdir(source) and not os.listdir(source):
            click.echo(f"Selected source directory {source} is empty!")
        elif os.path.isdir(source):
            click.echo(f"Setting source directory to: {source}")
            ctx['PES']['source'] = source
        else:
            click.echo(f"Unknown issue encountered while setting source "
                       f"directory to: {source}")
    if dest:
        if not os.path.exists(dest):
            click.echo(f"Creating destination directory: {dest}")
            os.makedirs(dest)
            ctx['PES']['dest'] = dest
        elif os.path.isdir(dest):
            click.echo(f"Setting destination directory to: {dest}")
            ctx['PES']['dest'] = dest
        else:
            click.echo(f"Unknown issue encountered while setting destination "
                       f"directory to: {dest}")
    return

@pic.command(name="setup")
@click.option('--move/--copy', '-m/-c', default=False,
              help="Move the files rather than copying (copies by default).")
def setup(move=False):
    """Set up the picture extractor by moving/copying.

    Before running this command, the 'config' command must be run to set the
    source and working directories.

    A flag is available on this command to choose whether to move or copy the
    files from the source to the working directory.
    """
    ctx = click.get_current_context().obj

    # check that required parameters are set
    source = ctx['PES'].get('source')
    working = ctx['PES'].get('working')
    if not source:
        raise click.UsageError("No source directory set. Please use the "
                               "'config' command to set the source directory "
                               "before running 'setup'.")
    if not working:
        raise click.UsageError("No working directory set. Please use the "
                               "'config' command to set the working directory "
                               "before running 'setup'.")

    # get current directory so we can return after moving files
    curdir = os.getcwd()

    # open the source directory so path parsing works correctly
    os.chdir(source)

    # find the files in the source directory
    source_files = os.listdir(source)
    istype = lambda f, t: ((k := filetype.guess(os.path.join(source, f)))
                           and k.mime.startswith(t))
    images = [f for f in source_files if istype(f, 'image')]
    videos = [f for f in source_files if istype(f, 'video')]

    click.echo(
        f"Found {len(images)} images and {len(videos)} videos in the source "
        f"directory.\n"
    )

    ext_img = click.prompt("Would you like to extract images", type=click.BOOL)
    if ext_img:
        img_expr = click.prompt(
            ("Enter a path expression (using '*.jpg', etc.) for your image "
             "set (use '*' to select all images)"),
            type=click.Path())
        sel_images = glob.glob(img_expr, root_dir=source)
        # ensure all files are images
        sel_images = [img for img in sel_images if istype(img, 'image')]
    else:
        sel_images = []
    click.echo(f"Selected {len(sel_images)} images.\n")

    ext_vid = click.prompt(
        f"How many videos would you like to extract (0 to {len(videos)})",
        type=click.IntRange(0, len(videos)))
    if ext_vid >= 1:
        click.echo("Available videos:")
        click.echo_via_pager([f"  {v}" for v in videos])
    sel_videos = []
    i = 0
    while i < ext_vid:
        vid = click.prompt(
            "Enter a video to extract from the source directory",
            type=click.Path(dir_okay=False, exists=True))
        # ensure file is a valid video
        if istype(vid, 'video'):
            sel_videos.append(vid)
            i += 1
        else:
            click.echo(f"The file you entered ({vid}) is not a video!")
    click.echo(f"Selected {len(sel_videos)} videos.\n")

    # navigate into the working directory to prevent broken paths
    os.chdir(working)

    # set up the workspace
    if sel_images:
        os.makedirs(f"{working}/input/images", exist_ok=True)
    for i in range(len(sel_videos)):
        os.makedirs(f"{working}/input/video{i}", exist_ok=True)
    os.makedirs(f"{working}/output", exist_ok=True)
    # for i in range(len(sel_videos) + bool(sel_images)):
    #     os.makedirs(f"{working}/output/set{i}", exist_ok=True)

    # move or copy files based on called options
    ufunc = shutil.move if move else shutil.copy

    # move or copy the images
    for img in sel_images:
        ufunc(os.path.join(source, img),
              os.path.join(working, "input/images", img))
    click.echo(f"{'Moved' if move else 'Copied'} {len(sel_images)} images to "
               f"working directory.\n")

    # move or copy the videos
    for i, vid in enumerate(sel_videos):
        ufunc(os.path.join(source, vid),
              os.path.join(working, f"input/video{i}", vid))
    click.echo(f"{'Moved' if move else 'Copied'} {len(sel_videos)} videos to "
               f"working directory.\n")

    # return to original directory (where the code was run)
    os.chdir(curdir)

def extract_video(v, output, n=30):
    """Extract images from a video"""
    # frame count and index initialization
    frame_index = 0
    frame_count = 0

    # loop through the video and save every nth frame
    while True:
        ret, frame = v.read()
        if not ret:
            # exit while loop when video ends
            break
        # save every nth frame
        if not frame_count % n:
            frame_fname = os.path.join(output, f"{frame_index:05}.jpg")
            cv2.imwrite(frame_fname, frame)
            frame_index += 1
        frame_count += 1

    # release video capture object
    v.release()
    return

@pic.command(name="extract")
def extract():
    """Set up the picture extractor by moving/copying.

    Before running this command, the 'config' command must be run to set the
    source and working directories.

    A flag is available on this command to choose whether to move or copy the
    files from the source to the working directory.
    """
    ctx = click.get_current_context().obj

    # check that required parameters are set
    working = ctx['PES'].get('working')
    if not working:
        raise click.UsageError("No working directory set. Please use the "
                               "'config' command to set the working directory "
                               "before running 'setup'.")

    # check that the setup step has been done correctly
    inp = 'input' in os.listdir(working)
    out = 'output' in os.listdir(working)
    if not inp and not out:
        raise click.UsageError("The working directory has not been properly "
                               "configured. Please run the 'setup' command "
                               "before running 'extract'.")

    # fetch the number of possible sets
    videos = sum(d.startswith('video') for d in os.listdir(f"{working}/input"))
    images = 'images' in os.listdir(f"{working}/input")
    max_sets = videos + images
    if not max_sets:
        raise click.UsageError("The working directory contains no input "
                               "material. Please check that you correctly ran "
                               "the 'setup' command.")

    # ask the user how many sets they want to extract
    set_count = click.prompt(
        "How many image sets would you like to extract",
        type=click.IntRange(0, max_sets))

    # set up available inputs
    available = set(os.listdir(f"{working}/input"))

    # loop over chosen set count and extract if necessary
    for i in range(set_count):
        # get chosen input set
        choice = click.prompt(
            "Enter the input you would like to extract to an image set",
            type=click.Choice(available))
        # remove input set from available inputs
        available -= {choice}
        # create the output set directory
        os.makedirs(f"{working}/output/set{i}", exist_ok=True)
        # extract images if video, else copy images
        if choice == 'images':
            for img in os.listdir(f"{working}/input/images"):
                shutil.copy(f"{working}/input/images/{img}",
                            f"{working}/output/set{i}/{img}")
        elif choice.startswith('video'):
            vname = os.listdir(f"{working}/input/{choice}")
            if not vname:
                raise click.UsageError(
                    f"No files exist in {working}/input/{choice}")
            vpath = f"{working}/input/{choice}/{vname[0]}"
            video = cv2.VideoCapture(vpath)
            extract_video(video, f"{working}/output/set{i}")

def remove_motion_blur(image_path, kernel_size=15):
    # Load the image
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    # Create a motion blur kernel (linear blur)
    kernel = np.zeros((kernel_size, kernel_size))
    kernel[int((kernel_size - 1)/2), :] = np.ones(kernel_size)
    kernel /= kernel_size  # Normalize the kernel

    # Apply Wiener filter for deblurring
    deblurred = signal.wiener(img, (5, 5))  # Wiener filter (5x5 neighborhood)

    # Normalize the result
    deblurred = np.clip(deblurred, 0, 255).astype(np.uint8)

    # Save and show the result
    cv2.imwrite("deblurred_image.jpg", deblurred)
    cv2.imshow("Deblurred Image", deblurred)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
