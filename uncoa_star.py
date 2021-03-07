#!/Users/pafana/software/anaconda3/bin/python

ver=210307

import os, re, sys

def find_star_column(col_name, starfile_name):
    '''
    finds specific column number of the star file
    '''
    f1=open(starfile_name, 'r')
    starlines = f1.readlines()
    for line in starlines:
        line_elements=line.split()
        if len(line_elements) < 3:
            #determine the column number:
            match1=re.search(r'%s #(\d+)' %col_name, line)
            if match1: col_number=int(match1.group(1))
            # check if the values are in the star file
    if col_number==None:
        print('\nERROR: no %s column found in the star file' %col_name)
        sys.exit(1)
    f1.close()
    return col_number

def main():
    files = sorted(os.listdir('.'))
    output_text='''
==================================== uncoa_star.py =================================================
uncoa_star.py multiplies X,Y coordinates from the star file by the given multiplication factor

Pavel Afanasyev
[version %s]
https://github.com/afanasyevp/cryoem_tools
====================================================================================================''' % (ver)
    print(output_text)
    coar_factor=int(input("Enter the coarsening factor in the images [1]: "))
    mult_factor=int(input("Enter the multiplication factor [2]: "))
    rootname=input("Enter a part of the filename (to avoid unnecessary files) [.star]: ")
    print()
    
    for file in files:
        if file[-5:] == '.star' and "%s" % rootname in file:
            new_file=file[:-5]+"_unbinned.star"
            print("%s file created" %new_file)
            f1=open(file, 'r')
            f2=open(new_file, 'w')
            lines=f1.readlines()
            for line in lines:
                line=line.strip()
                if line.startswith('data_'): # ignore STAR structure :) 
                    f2.write(line+'\n')
                elif line.startswith('loop_'): # still ignore
                    f2.write(line+'\n')
                elif line.startswith('_'):
                    if '_rlnCoordinateX' in line:
                        ind_rlnCoordinateX=find_star_column('_rlnCoordinateX', file)
                    elif '_rlnCoordinateY' in line:
                        ind_rlnCoordinateY=find_star_column('_rlnCoordinateY', file)
                    f2.write(line+'\n')
                elif len(line)==0: # ignore empty lines
                    f2.write(line+'\n')
                elif not line.startswith("#"):
                    line=line.split()
                    line[ind_rlnCoordinateX-1]=str(float(line[ind_rlnCoordinateX-1])*mult_factor)
                    line[ind_rlnCoordinateY-1]=str(float(line[ind_rlnCoordinateY-1])*mult_factor)
                    temp=' '.join(line)
                    f2.write(temp+'\n')
            f1.close()
            f2.close()

if __name__ == '__main__':
    main()
