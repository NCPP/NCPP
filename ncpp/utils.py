
def get_class( kls ):
    """ Utility function to retrieve a Class object from its fully qualified name."""
    
    parts = kls.split('.')
    module = ".".join(parts[:-1])
    m = __import__( module )
    for comp in parts[1:]:
        m = getattr(m, comp)            
    return m
