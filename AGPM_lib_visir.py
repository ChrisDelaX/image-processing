# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 07:22:40 2015

@author: ehuby + cdelacroix
"""

import os
import numpy as np
import scipy.optimize as opt
import scipy.special as spe
from astropy.io import fits         # fits file reading/writing
import matplotlib.pyplot as plt     
from matplotlib import cm           # palette for image display
import glob as glob
import AGPM_lib_visir as AGPM



def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)

def get_image_VISIR(k,path,obsA,obsB,center,rim,rbkg,filt,target,lb,seeing,offset,xOffset):
    
    cx,cy = center
    if offset==0:
        HDU_A = fits.open(glob.glob(path+'*'+obsA+'*.fits')[0])[1]
        HDU_B = fits.open(glob.glob(path+'*'+obsB+'*.fits')[0])[1]
        cx2,cy2 = cx,cy
        offset2 = 0
    else:
        HDU_A = fits.open(glob.glob(path+'*'+obsA+'*.fits')[0])[3] #[3] is the chopped image
        HDU_B = fits.open(glob.glob(path+'*'+obsB+'*.fits')[0])[3] #[3] is the chopped image
        PSF_nocor_A = HDU_A.data[cy-rim+offset:cy+rim+offset+1,cx-rim:cx+rim+1]
        PSF_nocor_B = HDU_B.data[cy-rim-offset:cy+rim-offset+1,cx-rim:cx+rim+1]
        (A,xa,ya,F) = AGPM.fit_airy_2D(-PSF_nocor_A)
        (A,xb,yb,F) = AGPM.fit_airy_2D(PSF_nocor_B)
        cx2 = cx + (xa+xb-2*rim)/2
        cy2 = cy + (ya+yb-2*rim)/2
        offset2 = offset + (ya-yb)/2.
    
    bkg_A = HDU_A.data[cy2-rbkg:cy2+rbkg+1,cx2-rbkg:cx2+rbkg+1]
    bkg_B = HDU_B.data[cy2-rbkg:cy2+rbkg+1,cx2-rbkg:cx2+rbkg+1]
    PSF_nocor_A = HDU_A.data[cy2-rim+offset2:cy2+rim+offset2+1,cx2-rim:cx2+rim+1]
    PSF_nocor_B = HDU_B.data[cy2-rim-offset2:cy2+rim-offset2+1,cx2-rim:cx2+rim+1]
    PSF_AGPM_A = HDU_A.data[cy2-rim:cy2+rim+1,cx2-rim:cx2+rim+1]
    PSF_AGPM_B = HDU_B.data[cy2-rim:cy2+rim+1,cx2-rim:cx2+rim+1]
    bkg = (bkg_B-bkg_A)/2.
    PSF_nocor = (PSF_nocor_B-PSF_nocor_A)/2.
    PSF_AGPM = -(PSF_AGPM_B-PSF_AGPM_A)/2.    


    return (bkg,PSF_nocor,PSF_AGPM,HDU_A,HDU_B)
    

def twoD_Gaussian((x, y), amplitude, xo, yo, sigma_x, sigma_y, theta, offset):
    ''' Model function. 2D Gaussian.
    '''    
    
    xo = float(xo)
    yo = float(yo)    
    a = (np.cos(theta)**2)/(2*sigma_x**2) + (np.sin(theta)**2)/(2*sigma_y**2)
    b = -(np.sin(2*theta))/(4*sigma_x**2) + (np.sin(2*theta))/(4*sigma_y**2)
    c = (np.sin(theta)**2)/(2*sigma_x**2) + (np.cos(theta)**2)/(2*sigma_y**2)
    g = offset + amplitude*np.exp( - (a*((x-xo)**2) + 2*b*(x-xo)*(y-yo) 
                            + c*((y-yo)**2)))
    return g.ravel()
    
def oneD_Gaussian(x, amplitude, xo, sigma_x):
    ''' Model function. 1D Gaussian.
    '''    
    
    xo = float(xo)
    #g = offset + amplitude*np.exp( ((x-xo)/(2*sigma_x))**2 )
    g = amplitude*np.exp( -((x-xo)/(np.sqrt(2)*sigma_x))**2 )
    
    #print(amplitude, xo, sigma_x)
    
    return g
    
def poly6(x, x0, a0, a1, a2, a3, a4, a5, a6):
    ''' Model function. Polynomial function up to 6th order.
    '''
    
    xx = x-x0
    y = a0 + a1*xx + a2*xx**2 + a3*xx**3 + a4*xx**4 + a5*xx**5 + a6*xx**6
    
    return y

def poly6odd(x, x0, a0, a2, a4, a6):
    ''' Model function. Polynomial function up to 6th order.
    '''
    xx = x-x0
    y = a0 + a2*xx**2 + a4*xx**4 + a6*xx**6
    return y

def twoD_Airy((x,y), amplitude, xo, yo, F):
    ''' Model function. 2D Airy.
    '''    

    r = np.sqrt((x-xo)**2+(y-yo)**2)*F
    
    nx=r.shape[1]
    ny=r.shape[0]    
    maxmap=np.where(r==0, np.ones((ny,nx)), np.zeros((ny,nx)))
    nbmax=np.sum(maxmap)
    if nbmax == 1:
        indmax=np.unravel_index(maxmap.argmax(), maxmap.shape)
        r[indmax]=1.
    elif nbmax > 1:
        print 'ERROR in twoD_Airy: several nulls'
    
    J=spe.jn(1, r)
    Airy=amplitude*(2*J/r)**2
    if nbmax == 1 :   
        Airy[indmax]=amplitude
    
    return Airy.ravel()

def oneD_Airy(x, amplitude, xo, F):
    ''' Model function. 1D Airy.
    '''

    r=(x-xo)*F
    nx=x.shape[0]
    
    maxmap=np.where(x==0, np.ones(nx), np.zeros(nx))
    nbmax=np.sum(maxmap)
    if nbmax == 1:
        indmax=np.argmax(maxmap)
        r[indmax]=1.
    elif nbmax > 1:
        print 'ERROR in oneD_Airy: several nulls'
    
    J=spe.jn(1, r)
    Airy=amplitude*(2*J/r)**2
    if nbmax == 1 :   
        Airy[indmax]=amplitude
    
    return Airy
    
def oneD_Airy_log(x, amplitude, xo, F):
    ''' Model function. 1D log10(Airy).
    '''    

    r=(x-xo)*F
    nx=x.shape[0]
    
    maxmap=np.where(r==0, np.ones(nx), np.zeros(nx))
    nbmax=np.sum(maxmap)
    if nbmax == 1:
        indmax=np.argmax(maxmap)
        r[indmax]=1.
    elif nbmax > 1:
        print 'ERROR in oneD_Airy: several nulls'
    
    J=spe.jn(1, r)
    Airy=amplitude*(2*J/r)**2
    if nbmax == 1 :   
        Airy[indmax]=amplitude
    
    return np.log10(Airy)

def fit_gauss_2D(img):
    ''' Fits a 2D Gaussian pattern on the image.
        
        Returns the best fit parameters of the Gaussian shape.
        
        See twoD_Gaussian((x, y), amplitude, xo, yo, sigma_x, sigma_y, theta, offset)
    '''

    nx=img.shape[1]
    ny=img.shape[0]
    x = np.linspace(0, nx-1, nx)
    y = np.linspace(0, ny-1, ny)
    x, y = np.meshgrid(x, y)

    init_xmax=np.unravel_index(img.argmax(), img.shape)[1]
    init_ymax=np.unravel_index(img.argmax(), img.shape)[0]
    initial_guess = (img.max(), init_xmax, init_ymax, 5, 5, 0, 0)
    popt, pcov = opt.curve_fit(twoD_Gaussian, (x, y), img.ravel(), 
                               p0=initial_guess)
    
    return popt

def fit_gauss_1D(y, x):
    ''' Fits a 1D Gaussian curve.
        
        Returns the best fit parameters of the Gaussian shape.
        
        See oneD_Gaussian(x, amplitude, xo, sigma_x, offset)
    '''

    #nx=y.shape[0]
    #x = np.linspace(0, nx-1, nx)

    init_xmax=x[y.argmax()]
    
    initial_guess = (y.max(), init_xmax, (x[-1]-x[0])/4.)
    popt, pcov = opt.curve_fit(oneD_Gaussian, x, y, p0=initial_guess)
    
    return popt
    
def fit_airy_2D(img, disp=0):
    ''' Fits a 2D Airy pattern on the image.
        
        Returns the best fit parameters of the Airy pattern.
        
        See twoD_Airy((x, y), amplitude, xo, yo, sigma_x, sigma_y, theta, offset)
    '''

    nx=img.shape[1]
    ny=img.shape[0]
    x = np.linspace(0, nx-1, nx)
    y = np.linspace(0, ny-1, ny)
    x, y = np.meshgrid(x, y)

    init_xmax=np.unravel_index(img.argmax(), img.shape)[1]
    init_ymax=np.unravel_index(img.argmax(), img.shape)[0]
    initial_guess = (img.max(), init_xmax, init_ymax, .4)
    #initial_guess = (img[init_xmax, init_ymax]  , init_xmax, init_ymax, .6)

    #plt.figure(27)
    #plt.imshow(twoD_Airy((x,y), img[init_xmax, init_ymax]  , init_xmax, init_ymax, .6).reshape(nx,ny))

    popt, pcov = opt.curve_fit(twoD_Airy, (x, y), img.ravel(), p0=initial_guess)
    
    if disp != 0:
        data_fitted = twoD_Airy((x, y), *popt)
        #offset=np.min(img)
        plt.figure(disp)
        plt.clf()
        plt.subplot(1,3,1)
        plt.imshow(data_fitted.reshape(nx,ny), interpolation='none', cmap=cm.Greys_r)
        plt.colorbar()
        plt.subplot(1,3,2)
        plt.plot(img[popt[1],:])
        plt.plot(data_fitted.reshape(nx,ny)[popt[1],:], 'r--')
        plt.yscale('log')
        plt.subplot(1,3,3)
        plt.plot(img[:,popt[2]])
        plt.plot(data_fitted.reshape(nx,ny)[:,popt[2]], 'r--')
        plt.yscale('log')
        
        plt.figure(disp+1)
        plt.clf()
        plt.subplot(121)
        plt.imshow(data_fitted.reshape(nx,ny), interpolation='none', cmap=cm.Greys_r)
        plt.colorbar()      
        P_fit=get_radial_profile(data_fitted.reshape(nx,ny), (popt[1], popt[2]), 1, disp=10)
        P_mes=get_radial_profile(img, (popt[1], popt[2]), 1, disp=0)        
        plt.subplot(122)        
        plt.plot(P_mes, 'b')
        plt.plot(P_fit, 'r--')
        plt.yscale('log')
        
        print '\n--- Airy disk fit results ---'
        print 'Amplitude ='+str(popt[0])
        print 'Position of the maximum: \nxo='+str(popt[1])+' nyo='+str(popt[2])
        print 'F factor='+str(popt[3])
        print '-----------------------------'
    
    return popt
    
def fit_airy_1Dlog(Y, disp=0, initial_guess=[0.,0.,0.]):
    "fit one D   "
    
    nx=Y.shape[0]
    x=np.linspace(0,nx-1,nx)
    
#    minval=np.min(Y)
#    Y-=minval
#    ampl=np.max(Y)
#    Y=Y/ampl
    
    Ylog=np.log10(Y)
    
    if np.sum(initial_guess) == 0. :
        initial_guess=(np.max(Y), np.argmax(Y), .5)
    
    popt, pcov = opt.curve_fit(oneD_Airy_log, x, Ylog, p0=initial_guess, sigma=1./Y**2)  
    
    if disp != 0:
        data_fitted=oneD_Airy_log(x, *popt)        
        plt.figure(disp)
        plt.clf()
        plt.plot(Ylog, 'b')
        plt.plot(x, data_fitted, 'r--')
    
    return popt
    
def fit_airy_1D(Y, disp=0, initial_guess=[0.,0.,0.]):
    "fit one D   "
    
    nx=Y.shape[0]
    x=np.linspace(0,nx-1,nx)
    
#    minval=np.min(Y)
#    Y-=minval
#    ampl=np.max(Y)
#    Y=Y/ampl
    
    if np.sum(initial_guess) == 0. :
        initial_guess=(np.max(Y), np.argmax(Y), .5)
    
    popt, pcov = opt.curve_fit(oneD_Airy, x, Y, p0=initial_guess, sigma=1./Y)  
    
    if disp != 0:
        data_fitted=oneD_Airy(x, *popt)        
        plt.figure(disp)
        plt.clf()
        plt.plot(Y, 'b')
        plt.yscale('log')
        plt.plot(x, data_fitted, 'r--')
    
    return popt
    
def get_r_dist(nx,ny,xo,yo):
    ''' Returns the array of dimensions (nx,ny) with values corresponding the
        distance from the center (xo,yo). 
    '''
    
    x = np.linspace(0, nx, nx)-xo-1
    y = np.linspace(0, ny, ny)-yo-1
    x, y = np.meshgrid(x, y)
    
    return np.sqrt(x**2+y**2)
    
def get_radial_profile(img, (xo,yo), nbin, disp=0):
    ''' Computes the mean radial profile of the image.
    
        img:
            2D image.
        (xo,yo):
            center for the annuli.
        nbin:
            width of the annuli in pixels
        disp:
            optional key word for displaying the images.
            Its value will serve as the window number that will be created.
    '''
    
    (nx,ny)=img.shape
    r=get_r_dist(nx,ny,xo,yo)    
    
    r_max = np.max(r) # radius of the image
    r_max = np.max(r[xo,:])
    
    npts=int(r_max/nbin)
    O=np.ones((nx,ny))
    Z=np.zeros((nx,ny))
    Profile=np.zeros(npts)
    
    if disp != 0:
        plt.figure(disp)
        plt.clf()
        plt.subplot(121)
        plt.plot(xo,yo, 'xw')
        plt.title('PSF')
        plt.title('Averaged radial profile')
        plt.xlabel('Distance from center (pixels)')    
        plt.imshow(img, interpolation='none')
        plt.colorbar()
        
        val_min=np.min(img)
        val_max=np.max(img)        
        
        for k in range(0,npts-1,1):
            M=np.where(r>nbin*k, O, Z)*np.where(r<nbin*(k+1), O, Z)
            Profile[k]=np.sum(img*M)/np.sum(M)
            
            plt.figure(disp)
            plt.subplot(121)
            plt.imshow(img, interpolation='none')
            plt.pause(.005)
            plt.imshow(img*M, interpolation='none', vmin=val_min, vmax=val_max)
            plt.pause(.005)            
            plt.subplot(122)
            plt.plot(Profile, 'rx')
            plt.yscale('log')
        
        plt.plot(Profile, 'r')
        plt.subplot(121)
        plt.imshow(img, interpolation='none', vmin=val_min, vmax=val_max)
    
    for k in range(0,npts-1,1):
        M=np.where(r>nbin*k, O, Z)*np.where(r<nbin*(k+1), O, Z)
        Profile[k]=np.sum(img*M)/np.sum(M)   
    
    return Profile