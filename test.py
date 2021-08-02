import re
import logging
import tempfile
import os, sys


from renishawWiRE import WDFReader
import matplotlib.pyplot as plt
import numpy as np

def peak_in_range(spectra, wn, range, method="max", **params):
    """Find the max intensity of peak within range
       method can be max, min, or mean
    """
    print ("spectra")
    print (spectra)
    print ("wn")
    print (wn)
    print ("cond")
    
    cond = np.where((wn >= range[0]) & (wn <= range[1]))[0]
    print (cond)
    spectra_cut = spectra[:, cond]
    print (spectra_cut)
    return getattr(np, method)(spectra_cut, axis=1, **params)


def process(inputfile):
    basename = os.path.basename(inputfile)
    #this part handles the metadata
    reader = WDFReader(inputfile)
    result = dict()
    result['title'] = reader.title
    result['application_name'] = reader.application_name
    result['application_version'] = reader.application_version
    result['count'] = reader.count 
    result['capacity'] = reader.capacity 
    result['point_per_spectrum'] = reader.point_per_spectrum
    result['scan_type'] = str(reader.scan_type) 
    result['measurement_type'] = str(reader.measurement_type) 
    result['spectral_unit'] = str(reader.spectral_unit) 
    result['xlist_unit'] = str(reader.xlist_unit) 
    result['xlist_length'] = reader.count 
    result['xlist_type'] = str(reader.xlist_type) 
    result['ylist_unit'] = str(reader.ylist_unit) 
    result['ylist_length'] = reader.ylist_length 
    result['ylist_type'] = str(reader.ylist_type)
    result['laser_length'] = reader.laser_length

    #### now for the thumbnail
    wn = reader.xdata 
    spectra = reader.spectra
    x = reader.xpos
    y = reader.ypos
    z = reader.zpos
    plot_generated = False
    plot_file = f"plot{basename}.png"
    if reader.measurement_type == 1:
        if reader.count == 1 and wn.shape == spectra.shape:
            plt.figure(figsize=(10, 6))
            plt.plot(wn, spectra, label="Spectrum 1")
            plt.xlabel(f"Wavenumber ({str(reader.xlist_unit)})")
            plt.ylabel("Intensity (ccd counts)")
            plt.title(f"Spectrum from {basename}")
            plt.tight_layout()
            plt.savefig(plot_file, dpi=100)
            plot_generated = True
            plt.close()
        else:
            print("Either input file {inputfile} has more than one spectrum (count > 1) or wn.shape!=xp.shape")
    elif reader.measurement_type == 2:
        if all([np.all(x == 0), np.all(y == 0), ~np.all(z == 0)]) and reader.count == z.shape[0]:
            print ("here -->")
            cond = np.where(spectra.mean(axis=1) > 0)[0]
            z = z[cond]
            spectra = spectra[cond, :]

            # Data processing
            spectra = spectra - spectra.min(axis=1, keepdims=True)
            # Simply get accumulated counts between 1560 and 1620 cm^-1
            peak_1 = peak_in_range(spectra, wn, range=[0, 500])
            peak_2 = peak_in_range(spectra, wn, range=[1000, 1550])
            ratio = peak_2 / peak_1

            # Level the spectra with baseline intensity
            plt.figure(figsize=(10, 6))
            plt.plot(z, peak_1 / peak_1.max(), "-o", label="G Peak")
            # plt.plot(z, peak_2 / peak_2.max(), label="2D")
            # plt.plot(z, ratio, label="2D/G")
            plt.xlabel("Z [{0}]".format(str(reader.zpos_unit)))
            plt.legend(loc=0)
            plt.ylabel("Normed Intensity")
            plt.title(f"Results from {basename}")
            plt.tight_layout()
            plt.savefig(plot_file, dpi=100)
            plt.close()
            plot_generated = True
        else:
            print ("Condition not met for measuremean_type=2 to generate plot")
    elif reader.measurement_type == 3:
        if wn.shape[0] == spectra.shape[1]:
            spectra = spectra - spectra.min(axis=1, keepdims=True)
            spectra = spectra.T
            plt.figure(figsize=(10, 6))
            for i in range(spectra.shape[1]):
                plt.plot(wn, spectra[:, i], label="{0:d}".format(i))
            plt.legend()
            plt.xlabel(f"Wavenumber ({str(reader.xlist_unit)})")
            plt.ylabel("Intensity (ccd counts)")
            plt.title(f"Spectra from {basename}")
            plt.tight_layout()
            plt.savefig(plot_file, dpi=100)
            plt.close()
        else:
            print ("Condition not met for measuremean_type=3 to generate plot")
    else:
        pass


if __name__ == "__main__":
    extractor = process(sys.argv[1])
