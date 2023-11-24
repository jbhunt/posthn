import re
import numpy as np
import pathlib as pl
from PIL import Image

def _parseFolderName(folder):
    """
    Extract the volume and chapter numbers from the name of the folder
    """

    lowered = folder.name.lower()
    chapterNumber, volumeNumber = None, None
    if bool(re.search('vol', lowered)):
        matches = re.findall('vol[^\d]*\d+', lowered)
        if len(matches) == 1:
            substring = matches.pop()
            matches = re.findall('(\d+(?:\.\d+)?)', substring)
            if len(matches) == 1:
                volumeNumber = float(matches.pop())

    if bool(re.search('ch', lowered)):
        matches = re.findall('ch[^\d]*\d+', lowered)
        if len(matches) == 1:
            substring = matches.pop()
            matches = re.findall('(\d+(?:\.\d+)?)', substring)
            if len(matches) == 1:
                chapterNumber = float(matches.pop())

    if chapterNumber is None:
        raise Exception(f'Could not extract chapter number from folder: {folder.name}')

    return volumeNumber, chapterNumber

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
        volumeNumber, chapterNumber = _parseFolderName(
            subfolder,
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
        print(f'Collecting images from folder: {subfolder.name}')
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
            filename = f'{mangaTitle} (Chapters {chapterRange[0]} - {chapterRange[1]}).pdf'
    dst = outputFolder.joinpath(filename)

    # Create the pdf
    print(f'Generating pdf ...', end='\r')
    imageObjects[0].save(
        str(dst), "PDF", quality=95, save_all=True, append_images=imageObjects[1:]
    )    
    print(f'Generating pdf ... Done!')

    return dst