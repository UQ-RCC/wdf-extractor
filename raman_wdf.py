import pyclowder
import re
import logging
import tempfile
import os
import subprocess

from pyclowder.extractors import Extractor
import pyclowder.files

from renishawWiRE import WDFReader
import matplotlib.pyplot as plt
import numpy as np

def peak_in_range(spectra, wn, range, method="max", **params):
    """Find the max intensity of peak within range
       method can be max, min, or mean
    """
    cond = np.where((wn >= range[0]) & (wn <= range[1]))[0]
    spectra_cut = spectra[:, cond]
    return getattr(np, method)(spectra_cut, axis=1, **params)

class RenishawWiRERamanXtractor(Extractor):
    """WDF extractor."""
    def __init__(self):
        Extractor.__init__(self)

        self.setup()

        # setup logging for the exctractor
        logging.getLogger('pyclowder').setLevel(logging.DEBUG)
        logging.getLogger('__main__').setLevel(logging.DEBUG)

    def process_message(self, connector, host, secret_key, resource, parameters):
        # Process the file and upload the results

        logger = logging.getLogger(__name__)
        inputfile = resource["local_paths"][0]
        basename = os.path.basename(inputfile)
        file_id = resource['id']

        #this part handles the metadata
        try:
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

            metadata = self.get_metadata(result, 'file', file_id, host)
            logger.debug(metadata)
            # upload metadata
            pyclowder.files.upload_metadata(connector, host, secret_key, file_id, metadata)

            #### now for the thumbnail
            wn = reader.xdata 
            spectra = reader.spectra
            x = reader.xpos
            y = reader.ypos
            z = reader.zpos
            plot_generated = False
            plot_file = f"plot{file_id}.png"
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
                print("Depth profile is not supported yet")
                # if all([np.all(x == 0), np.all(y == 0), ~np.all(z == 0)]) and reader.count == z.shape[0]:
                #     cond = np.where(spectra.mean(axis=1) > 0)[0]
                #     z = z[cond]
                #     spectra = spectra[cond, :]

                #     # Data processing
                #     spectra = spectra - spectra.min(axis=1, keepdims=True)
                #     # Simply get accumulated counts between 1560 and 1620 cm^-1
                #     peak_1 = peak_in_range(spectra, wn, range=[1560, 1620])
                #     peak_2 = peak_in_range(spectra, wn, range=[2650, 2750])
                #     ratio = peak_2 / peak_1

                #     # Level the spectra with baseline intensity
                #     plt.figure(figsize=(10, 6))
                #     plt.plot(z, peak_1 / peak_1.max(), "-o", label="G Peak")
                #     # plt.plot(z, peak_2 / peak_2.max(), label="2D")
                #     # plt.plot(z, ratio, label="2D/G")
                #     plt.xlabel("Z [{0}]".format(str(reader.zpos_unit)))
                #     plt.legend(loc=0)
                #     plt.ylabel("Normed Intensity")
                #     plt.title(f"Results from {basename}")
                #     plt.tight_layout()
                #     plt.savefig(plot_file, dpi=100)
                #     plt.close()
                #     plot_generated = True
                # else:
                #     print ("Condition not met for measuremean_type=2 to generate plot")
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

            # only upload thumbnail if plot generated
            if plot_generated:
                try:
                    pyclowder.files.upload_thumbnail(connector, host, secret_key, file_id, plot_file)
                except Exception as e:
                    logger.error(e)
                try:
                    os.remove(plot_file)
                except Exception as e:
                    logger.error("Could not delete temp file", e)
        except Exception as e:
            logger.error(f"Error processing file: {inputfile}, fileid: {file_id}. error: ", e)


if __name__ == "__main__":
    extractor = RenishawWiRERamanXtractor()
    extractor.start()