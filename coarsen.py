#!/usr/bin/env python3

ver='210823'
import subprocess, sys, argparse

def get_files(path, pattern):
    '''
    get the list of the .mrc files in the given path 
    '''
    p=subprocess.Popen('find %s -name "*%s"' %(path, pattern), stdout=subprocess.PIPE, shell=True)
    (mrc_files, err) = p.communicate()
    p_status = p.wait()
    #print('%i files found in the "%s" folder'%(len(mrc_files.decode('ascii').split()), path))
    return mrc_files.decode('ascii')

def relion_resize(coa_factor, pix_size, mrcs, mrcs_processed):
    count=1   
    for mrc in mrcs:
        if (mrc[:-4] + "_c%d" %coa_factor + ".mrc") not in mrcs_processed:
            if mrc[-6-len(str(coa_factor)):] != "_c%d.mrc"%coa_factor:
                #print(mrc, mrc[-6-len(str(coa_factor)):])
                output=mrc[:-4]+ "_c%d" %coa_factor + ".mrc"
                print(" => working on: ", output, "   Progress: %.2f %%"%(100*count/(len(mrcs)-len(mrcs_processed))))
                p=subprocess.Popen('relion_image_handler --i %s --o %s --angpix %f --rescale_angpix %f ' %(mrc, output, pix_size, pix_size*coa_factor), stdout=subprocess.PIPE, shell=True)
                (output, err) = p.communicate()  
                p_status = p.wait()
                count+=1

def main():
    output_text='''
==================================== coarsen.py =================================================
coarsen.py bins motion-corrected micrographs in the given folder/path by a given factor
 
Make sure that relion is sourced

[version %s]
Written and tested in python3.7
Pavel Afanasyev
https://github.com/afanasyevp/cryoem_tools
=================================================================================================''' % ver 

    parser = argparse.ArgumentParser(description="")
    add=parser.add_argument
    add('--path', default="./", help="Path with your files. Default value: ./ ")
    add('--coa', default="8", help="Coarsening factor. Default value: 8")
    add('--pix', default="1", help="Pixel size. Default value: 1")
    add('--label', default=".mrc", help="Suffix in the filename to search for. Default value: .mrc")
    args = parser.parse_args()
    print(output_text)
    parser.print_help()
    print("\nExample: coarsen.py --path ./ --coa 8 --pix 0.85 --label .mrc")
    print("")
    coa_factor=int(args.coa)
    pix_size=float(args.pix)
    path=args.path
    label=args.label
    mrcs=get_files(path, label).split()
    #print(mrcs)
    mrcs_processed=get_files(path, "_c%d.mrc" %coa_factor).split()
    relion_resize(coa_factor, pix_size, mrcs, mrcs_processed)
if __name__ == '__main__':
    main()

