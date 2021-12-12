Our API can be sent requests at https://x-ripple-333802.uc.r.appspot.com/. A front end for our application exists at <FRONTEND URL>. 
When accessing the API, always ensure to check the returned data, as the ID sent in may not be (most likely, won't be) the official ID of the package stored in the registry. 
All version numbers are to be of the form (major).(minor).(patch), i.e. "1.0.0". Ensure that the name you assign to a package does NOT end in a number. For example, "Underscore" is allowed, but "Underscore123" is not.
Suppported endpoints are:
    /package, w/ methods [POST]
    /package/<id>, w methods [DELETE, GET, PUT]