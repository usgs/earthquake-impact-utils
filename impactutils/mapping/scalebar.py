#for scale function
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from cartopy.mpl.geoaxes import GeoAxes
import cartopy

#CONSTANTS
BAR_HEIGHT_FONT = 0.75 #bar height in fontsize units
MAX_BAR_HEIGHT = 0.5 #maximum bar height in inches
POINTS_TO_INCHES = 1/72 #inches in one point
TICK_FRACTION = 0.3 #how much of a fontsize should tick height be?
GAP_FRACTION = 0.3 #how much of a fontsize should tick gap be?
BAR_WIDTH_FRACTION = 0.25 #how wide should the default bar be
DD2METERS = 111191.0
METERS2MILES = 3.28/5280
METERS2KM = 1/1000

#the default set of lengths (keys) and number of divisions (values)
LENGTHS = {4:4,
          10:2,
          12:4,
          15:3,
          20:4,
          30:3,
          40:4,
          75:3,
          100:4,
          120:4,
          150:3,
          200:4,
          240:6,
          300:6,
          400:4,
          600:6,
          750:3,
          1000:4,
          2000:4,
          4000:4,
          6000:6,
          10000:4,
          20000:4,
          40000:4,
          60000:6,
          75000:3,
          100000:4,
          200000:4,}

#Proj4 supported units and their conversion factor to meters
UNITS = {'km': 1000.,
         'm': 1.,
         'dm': 1/10,
         'cm': 1/100,
         'mm': 1/1000,
         'kmi': 1852.0,
         'in': 0.0254,
         'ft': 0.3048,
         'yd': 0.9144,
         'mi': 1609.344,
         'fath': 1.8288,
         'ch': 20.1168,
         'link': 0.201168,
         'us-in': 1./39.37,
         'us-ft': 0.304800609601219,
         'us-yd': 0.914401828803658,
         'us-ch': 20.11684023368047,
         'us-mi': 1609.347218694437,
         'ind-yd': 0.91439523,
         'ind-ft': 0.30479841,
         'ind-ch': 20.11669506}

def draw_scale(ax,pos='ll',padx=0.1,pady=0.1,font_size=None,units='km',zorder=20,
               bar_length=None,divisions=None):
    """Draw a scale bar on an axes, choosing the best defaults possible.
    
    Default behaviors:
     - The height of the bar will be relative to the font size.
     - The length of the tick on the bottom of the bar will be 0.5 * font_size
     - The gap between the tick and the top of the tick label will be 0.5 * font_size
     - The width of the bar will be determined choosing from a list of lengths 
       the length that is closest to 0.25 * map width.
     - The number of divisions will be associated with the chosen length.
     
    :param ax:
      Cartopy GeoAxes object.
    :param pos:
      String, one of ('ll','lr','ul','ur') (lower left, lower right, etc.)
    :param padx:
      For pos of 'll','ul': 
        - The float distance in axes units between left axis edge and left edge of
          scalebar.
      For pos of 'lr','ur':
        - The float distance in axes units between right axis edge and right edge of
          scalebar.
      Axes units range from 0 to 1.
    :param pady:
      For pos of 'll','lr': 
        - The float distance in axes units between bottom axis edge and bottom edge of
          scalebar.
      For pos of 'ul','ur':
        - The float distance in axes units between top axis edge and top edge of
          scalebar.
      Axes units range from 0 to 1.
    :param font_size:
      Int, None means that configured default font will be chosen.
    :param units:
      String, one of:
       - km Kilometer
       - m Meter
       - dm Decimeter
       - cm Centimeter
       - mm Millimeter
       - kmi International Nautical Mile
       - in International Inch
       - ft International Foot
       - yd International Yard
       - mi International Statute Mile
       - fath International Fathom
       - ch International Chain
       - link International Link
       - us-in U.S. Surveyor's Inch
       - us-ft U.S. Surveyor's Foot
       - us-yd U.S. Surveyor's Yard
       - us-ch U.S. Surveyor's Chain
       - us-mi U.S. Surveyor's Statute Mile
       - ind-yd Indian Yard
       - ind-ft Indian Foot
       - ind-ch Indian Chain
    :param zorder:
      Integer, matplotlib plotting order (higher values are plotted later.)
    :param bar_length:
      Float value (in 'units' units) to override the default bar length as 
      described above.  If this parameter is set, then divisions 
      must ALSO be set.  Caveat emptor.
    :param divisions:
      Integer value to override the default number of bar divisions as described 
      above.  Allowable divisions values are: [2,3,4,5,6]. If this parameter is set, 
      then bar_length must ALSO be set.  Caveat emptor.
    """
    hasbar = bar_length is not None
    hasdiv = divisions is not None
    if hasbar+hasdiv != 0 and hasbar+hasdiv != 2:
        raise Exception('You must specify BOTH bar_length AND divisions.')

    if divisions is not None:
        if divisions not in [2,3,4,5,6]:
            raise Exception('Divisions must be an integer in the range 2-6.')
    
    #check units
    if units not in UNITS:
        raise Exception('Input scale bar units must be either "km" or "mi"')
        
    #check position
    if pos not in ['ll','lr','ul','ur']:
        raise Exception("Input scale bar position must be one of 'll','lr','ul','ur'")
    
    #Verify that the input axes are in fact GeoAxes
    if not isinstance(ax,GeoAxes):
        raise Exception('Input axes object must be a Cartopy GeoAxes.')
        
    #Get the left, right, bottom, top edges in data units
    xmin,xmax = ax.get_xlim()
    ymin,ymax = ax.get_ylim()
        
    #Get the factor that converts the data units into meters
    if not isinstance(ax.projection,cartopy.crs.PlateCarree):
        if 'units' in ax.projection.proj4_params:
            proj_units = ax.projection.proj4_params['units']
            dataunits_to_meters = UNITS[proj_units]
        else:
            proj_units = 'm'
            dataunits_to_meters = UNITS[proj_units]
    else:
        #this is PlateCaree, which has no projection
        proj_units = 'dd'
        clat = ymin + (ymax-ymin)/2
        dataunits_to_meters = DD2METERS * np.cos(np.radians(clat)) #true at center of map
    meters_to_dataunits = 1/dataunits_to_meters
    
    #Get the figure object from the axes
    fig = ax.figure
    
    #Get the size of the figure in inches
    width_in,height_in = ax.figure.get_size_inches()
    
    #what is the transform object between the axes and display coordinates?
    ax2disp = ax.transAxes
    #what is the transform object between the display and data coordinates?
    disp2data = ax.transData.inverted()
    #what is the transform object between the display and figure coordinates?
    disp2fig = fig.transFigure.inverted()
    #what is the transform object between the figure and display coordinates?
    fig2disp = fig.transFigure

    #what is the font size?
    if font_size is None:
        font_size = matplotlib.rcParams['font.size']
    
    #what is bar height in data units?
    bar_height_inches = font_size * POINTS_TO_INCHES * BAR_HEIGHT_FONT
    bar_height_figure = bar_height_inches / height_in
    left_data,bottom_data = disp2data.transform(fig2disp.transform((0,0)))
    left_data,top_data = disp2data.transform(fig2disp.transform((0,bar_height_figure)))
    bar_height = top_data - bottom_data
    bar_height_axes = bar_height / (ymax-ymin)
        
    #what is the tick height in data units?
    tick_height_fig = (font_size * POINTS_TO_INCHES) * TICK_FRACTION / height_in
    left_data,bottom_data = disp2data.transform(fig2disp.transform((0,0)))
    left_data,top_data = disp2data.transform(fig2disp.transform((0,tick_height_fig)))
    tick_height = top_data - bottom_data
    
    #what is the tick gap in data units?
    gap_height_fig = (font_size * POINTS_TO_INCHES) * GAP_FRACTION / height_in
    left_data,bottom_data = disp2data.transform(fig2disp.transform((0,0)))
    left_data,top_data = disp2data.transform(fig2disp.transform((0,gap_height_fig)))
    gap_height = top_data - bottom_data
    
    
    #what is the bar length data units?
    if bar_length is None:
        lengths = np.array(list(LENGTHS.keys()))
        map_width_data = xmax - xmin
        map_width_meters = map_width_data * dataunits_to_meters
        map_width_scale_units = map_width_meters * 1/UNITS[units]
        qmap_width_scale_units = map_width_scale_units * BAR_WIDTH_FRACTION
        bar_length = lengths[np.argmin(np.abs(qmap_width_scale_units - lengths))] #in input units
        divisions = LENGTHS[bar_length]
        
    bar_length_data = bar_length * UNITS[units] * meters_to_dataunits
    bar_length_axes = bar_length_data/map_width_data
        
    #where is the scale bar going to be located (in axes units)?
    if pos == 'ul':
        bar_left_axes = padx
        bar_top_axes = 1.0 - pady
        bar_right_axes = bar_left_axes + bar_length_axes
        bar_bottom_axes = bar_top_axes - bar_height_axes
    if pos == 'll':
        bar_left_axes = padx
        bar_bottom_axes = pady
        bar_right_axes = bar_left_axes + bar_length_axes
        bar_top_axes = bar_bottom_axes + bar_height_axes
    if pos == 'ur':
        bar_right_axes = 1.0 - padx
        bar_left_axes = bar_right_axes - bar_length_axes
        bar_top_axes = 1.0 - pady
        bar_bottom_axes = bar_top_axes - bar_height_axes
    if pos == 'lr':
        bar_right_axes = 1.0 - padx
        bar_left_axes = bar_right_axes - bar_length_axes
        bar_bottom_axes = pady
        bar_top_axes = bar_bottom_axes + bar_height_axes

    #convert scale bar location to data units
    bar_left,bar_bottom = disp2data.transform(ax2disp.transform((bar_left_axes,bar_bottom_axes)))

    #figure out the edges of the whole scale bar
    bar_right = bar_left + bar_length_data
    bar_top = bar_bottom + bar_height
    rectx = [bar_left,bar_right,bar_right,bar_left,bar_left]
    recty = [bar_top,bar_top,bar_bottom,bar_bottom,bar_top]
    
    #draw the desired units across the top of the scale bar in the middle
    ux = bar_left + (bar_length_data/2)
    uy = bar_top + gap_height
    plt.text(ux,uy,units,ha='center',fontsize=font_size)

    #now draw the divisions
    #odd number divisions only label the ends
    #even numbers label every other tick
    is_div_even = divisions % 2 == 0
    for i in range(0,divisions):
        left_edge = bar_left + (bar_length_data/divisions)*i
        right_edge = left_edge + bar_length_data/divisions
        barx = [left_edge,right_edge,right_edge,left_edge,left_edge]
        if i % 2:
            #we're odd, draw black bar
            color = 'black'
        else:
            color = 'white'
            scale_tick = '%i' % (i*(bar_length/divisions))
            if is_div_even or i == 0: #if we have an even number of divisions, draw every other tick mark
                #draw the tick
                ax.plot([left_edge,left_edge],[bar_bottom,bar_bottom-tick_height],
                        'k',zorder=zorder)
                #draw the tick label
                ax.text(left_edge,bar_bottom-(tick_height+gap_height),'%s' % scale_tick,
                        ha='center',zorder=zorder,va='top',fontsize=font_size)
            
        ax.fill(barx,recty,color,zorder=zorder)
    #draw the last tick mark and number
    ax.text(bar_left+bar_length_data,bar_bottom-(tick_height+gap_height),'%i' % bar_length,
            ha='center',zorder=zorder,va='top',fontsize=font_size)
    left = bar_left+bar_length_data
    bottom = bar_bottom-tick_height
    top = bar_bottom
    ax.plot([left,left],[bottom,top],'k',zorder=zorder)

    #draw the outline of the scale bar
    ax.plot(rectx,recty,'black',zorder=zorder)
    
