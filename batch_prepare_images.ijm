//batch_prepare_images.ijm
version=220114;
print("");
print("================== batch_prepare_images.ijm ==================");
print("Fiji macro for batch image preparation for reports.");
print("Currently implemented:  Binning  and auto B&C.");
print("For czi: tick Windowless option in Bio-Formats=> Bio-Formats Plugins Configuration.");
print("If you use Mac, specify the path with your images in the second appearing window.");
print("Version: "+version);
print("By Pavel Afanasyev");
print("Please report bugs/issues to https://github.com/afanasyevp/cryoem_tools");
print("=====================================================");
print(" => Starting the script @ " + now() );

//Dialog with input parameters
scaleFactor=0.25;
suffix="_binned";
output_folder="binned_images"
extension=newArray("czi","jpg","JPG","jpeg","JPEG","mrc","png","PNG","tif","tiff");
Dialog.create("File format");
Dialog.addChoice("Specify file format:", extension);
Dialog.addNumber("Specify scale factor:", scaleFactor);
Dialog.addString("Output suffix:", suffix);
Dialog.addString("Output folder name:", output_folder);
Dialog.addCheckbox("Auto B&C", true);
Dialog.show();
suffix = Dialog.getString();
extension = Dialog.getChoice();
scaleFactor = Dialog.getNumber();
autoGreyScale = Dialog.getCheckbox();
output_folder = Dialog.getString();
//print("suffix :", suffix);
//print("output_folder: ", output_folder)

//Dialog with path
//setOption("JFileChooser", true); // enable for MacOS
dir  = getDirectory("Select a directory containing one or several ."+extension+" files.");
NewDir=dir+output_folder+"/";
if (File.isDirectory(NewDir)) {
    print(" => ERROR! Folder " + NewDir+" already exists! Please change your input!");
    exit("ERROR! "+ NewDir+" already exists! Please change your input!");
}
File.makeDirectory(NewDir);
print(" => created"+NewDir+" directory");

files  = getFileList(dir);
counter=0;
for (j=0; j<lengthOf(files);j+=1) {
    if(endsWith(files[j], "."+extension)) { 
        counter+=1;
    }   
}
print(" => "+counter+" "+extension+" files "+"were found in "+dir);

//Operations
for (j=0; j<lengthOf(files);j+=1) {
    if(endsWith(files[j], "."+extension)) {  
        open(dir+files[j]);  
        image1 = getTitle();  
        selectWindow(image1);   
        run("Scale...", "x="+scaleFactor+" y="+scaleFactor+" z=1.0  depth=3 interpolation=Bilinear average create"); 
        if (autoGreyScale) {
        //run("Brightness/Contrast...");
        run("Enhance Contrast", "saturated=0.35");
        wait(10); // increase if there are issues with too fast saving
        }
        dotIndex = indexOf( files[j], "." ); 
        baseName = substring( files[j], 0, dotIndex );
        NewName=baseName+suffix+".jpg";
        print(" => saving "+NewDir+NewName);
        saveAs("Jpeg", NewDir+NewName);
        run("Close All");
    }
}
print(" => Finishing the script @ "+now());

function now(){
	getDateAndTime(year, month, dayOfWeek, dayOfMonth, hour, minute, second, msec);
	nowValue = ""+IJ.pad(hour,2)+":"+IJ.pad(minute,2)+":"+IJ.pad(second,2);
	return nowValue;
}
print("");

