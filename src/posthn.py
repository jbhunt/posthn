import re
import numpy as np
import pathlib as pl
from PIL import Image

chapterLabelingPatternSets = [
    ('Ch\.\s\d\.\d{2}', '\d\.\d{2}'), # Example: Ch. 0.01
    ('Ch\.\s\d+', '\d+') # Example: Ch. 26
]

def _getChapterNumber(
    folder,
    chapterLabelingPatternSet=None
    ):
    """
    Identify the chapter number
    """

    # I'm using a global variables (so sue me)
    global chapterLabelingPatternSets

    # Insert the user-specified pattern set
    if chapterLabelingPatternSet is not None:
        chapterLabelingPatternSets.insert(
            0,
            chapterLabelingPatternSet,
        )

    # Search for the chapter number using each set of patterns
    chapterNumberIdentified = False
    for patternSet in chapterLabelingPatternSets:
        string = folder.name
        for i, pattern in enumerate(patternSet):
            matches = re.findall(pattern, string)
            if len(matches) != 1:
                break
            string = matches.pop()
            if i == len(patternSet) - 1:
                chapterNumberIdentified = True

        # Break out of the search: one of the pattern sets worked
        if chapterNumberIdentified:
            break

    # Make sure to remove the user-specificed pattern set
    if chapterLabelingPatternSet is not None:
        chapterLabelingPatternSets.remove(
            chapterLabelingPatternSet
        )

    #
    if string == folder.name:
        raise Exception(f'Failed to identify chapter number for folder: {folder.name}')

    return float(string)

def _collectImages(folder):
    """
    Collect images and identify their ordering
    """

    imageNumbers = list()
    imageFiles = list()
    for file in folder.iterdir():
        imageNumber = int(file.name.strip(file.suffix))
        imageNumbers.append(imageNumber)
        imageFiles.append(file)

    #
    imageIndex = np.argsort(imageNumbers)

    return imageFiles, imageIndex

def createPortableDocument(
    folder,
    filename=None,
    outputFolder=None,
    mangaTitle=None,
    chapterLabelingPatternSet=None
    ):
    """
    Combine images from each chapter into a pdf
    """

    # Range of chapter numbers
    chapterRange = [np.inf, -np.inf]

    # Determine the order of chapters
    chapterNumbers = list()
    subfolders = [sf for sf in folder.iterdir() if sf.is_dir()]
    for subfolder in subfolders:
        if subfolder.is_dir() == False:
            continue
        chapterNumber = _getChapterNumber(
            subfolder,
            chapterLabelingPatternSet=chapterLabelingPatternSet
        )
        if chapterNumber < chapterRange[0]:
            chapterRange[0] = chapterNumber
        if chapterNumber > chapterRange[1]:
            chapterRange[1] = chapterNumber
        chapterNumbers.append(chapterNumber)
    chapterIndex = np.argsort(chapterNumbers)

    # Create a list of PIL Image objects
    imageObjects = list()
    for i in chapterIndex:
        subfolder = subfolders[i]
        imageFiles, imageIndex = _collectImages(subfolder)
        for i in imageIndex:
            imageObject = Image.open(str(imageFiles[i])).convert('L')
            imageObjects.append(imageObject)

    # Define the filepath to the pdf
    if outputFolder is None:
        outputFolder = folder
    if filename is None:
        if mangaTitle is None:
            filename = f'omnibus (Chapters {chapterRange[0]} - {chapterRange[1]}).pdf'
        else:
            filename = f'{mangaTitle} omnibus (Chapters {chapterRange[0]} - {chapterRange[1]}).pdf'
    dst = outputFolder.joinpath(filename)

    # Create the pdf
    imageObjects[0].save(
        str(dst), "PDF", quality=95, save_all=True, append_images=imageObjects[1:]
    )    

    return dst