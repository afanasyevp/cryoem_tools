#!/Applications/anaconda/bin/python

ver=200604
import sys
import matplotlib.pyplot as plt
import argparse
import xml.etree.ElementTree as ET
import numpy as np
import xml.etree.ElementTree as ET
from xml.dom import minidom

def import_fscFile_relion(fscFile, pix):
    fscVal=[]
    res=[]
    fracOfNq=[]
    xmldata = minidom.parse("%s" %fscFile)
    fsc_items_list=xmldata.getElementsByTagName("coordinate")
    #print(fsc_items_list)
    for i in fsc_items_list:
        x = i.getElementsByTagName("x")
        y = i.getElementsByTagName("y")
        fscVal.append(float(y[0].childNodes[0].nodeValue))
        res.append(1/float(x[0].childNodes[0].nodeValue))
        fracOfNq.append(2*pix*float(x[0].childNodes[0].nodeValue) )
    return fscVal, res, fracOfNq
       
def import_fscFile_cistem(fscFile, pix):
    f1=open(fscFile, 'Ur')
    lines = f1.readlines()
    fscVal=[]
    res=[]
    fracOfNq=[]
    for line in lines[5:-1]:
        values=line.split()
        res.append(float(values[1]))
        fscVal.append(float(values[4]))
        fracOfNq.append(2*pix/float(values[1]))
    f1.close()
    return fscVal, res, fracOfNq
   
def main():
    output_text='''

======================================== plot_fsc.py ============================================
 
Returns FSC from the cisTEM fsc.txt file or relion postprocess_fsc.xml

Example for cisTEM: plot_fsc.py --i fsc1.txt fsc2.txt fsc3.txt --pix 1.09 
Example for relion: plot_fsc.py --i postprocess_fsc.xml --pix 1.09

[version %s]
Written and tested in python3.7

Pavel Afanasyev
https://github.com/afanasyevp/cryoem_tools
=================================================================================================
''' % ver 
    parser = argparse.ArgumentParser(description="")
    add=parser.add_argument
    add('--i', nargs="+",  help="Saved FSC table from cisTEM software")
    add('--pix', default='1', help="Pixel size. Default value: 1 A/pix")
    args = parser.parse_args()
    print(output_text)
    if len(sys.argv) == 1:
        #parser.print_help()
        sys.exit(2)
    if not args.i:
        print("No input file given.")
        #parser.print_help()
        sys.exit(2)
    else:
        fscFiles = args.i 
    if not args.pix:
        pix = float(args.pix)
        print("No pixel size given. Pixel size is considered 1A/pix")
    else:
        pix=float(args.pix)
    plt.figure()
    plt.xlabel('Fraction of Nyquist', fontweight="bold")
    plt.ylabel('FSC', fontweight="bold")
    plt.title('Fourier Shell Correlation', fontweight="bold")
    plt.xlim(right=1)  # adjust the right leaving left unchanged
    plt.xlim(left=0)  # adjust the left leaving right unchanged
    plt.ylim(top=1)  # adjust the top leaving bottom unchanged
    plt.ylim(bottom=0)  # adjust the bottom leaving top unchanged
    if len(fscFiles) == 1:
        if fscFiles[0][-4:] == '.txt':
            fscVal, res, fracOfNq = import_fscFile_cistem(fscFiles[0], pix)
        elif fscFiles[0][-4:] == '.xml':
            fscVal, res, fracOfNq = import_fscFile_relion(fscFiles[0], pix)
        else:
            print("ERROR: %s file is not a standard input" %fscFiles[0])
            sys.exit(2)
        plt.plot(fracOfNq, fscVal, color='#4bd1a0', linewidth=2)
    else: 
        for fscFile in fscFiles:
            if fscFile[-4:] == '.txt':
                fscVal, res, fracOfNq = import_fscFile_cistem(fscFile, pix)
            elif fscFile[-4:] == '.xml':
                fscVal, res, fracOfNq = import_fscFile_relion(fscFile, pix)
            else:
                print("ERROR: %s file is not a standard input" %fscFile)
                sys.exit(2)
            plt.plot(fracOfNq, fscVal, linewidth=2) 

    from matplotlib.ticker import FixedLocator, FixedFormatter
    ax = plt.gca()
    x_formatter = FixedFormatter(["", "", "0.2", "",  "0.4", "", "0.6", "", "0.8","", "1"])
    y_formatter = FixedFormatter(["0", "", "0.143", "0.2", "","0.4","", "0.6", "", "0.8", "","1"])
    x_locator = FixedLocator([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1])
    y_locator = FixedLocator([0, 0.1, 0.143, 0.2, 0.3,  0.4,0.5,  0.6,0.7, 0.8,0.9, 1])
    plt.plot([0, 1], [0.143, 0.143], linewidth=1, color='black')
    ax.xaxis.set_major_formatter(x_formatter)
    ax.yaxis.set_major_formatter(y_formatter)
    ax.xaxis.set_major_locator(x_locator)
    ax.yaxis.set_major_locator(y_locator)
    plt.grid(linestyle='-', linewidth=0.5)
    plt.show()
    
if __name__ == '__main__':
    main()

