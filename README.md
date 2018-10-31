# simple_swa_demo
This application is meant to provide a basic web UI for showing Okta's SWA and on-premise provisioning functionality.

It is a simple django application, leveraging the pre-delivered django authorization model, which includes simple forms-based authentication, as well as a basic user store based upon sqlite.

In addition, this project has a SCIM endpoint for use in provisioning user accounts and groups to/from the default sqlite database based upon information in Okta.

This project is not intended to be run alone- it's meant to be used as part of a docker setup.  Please refer to the following repository for instructions on how to stand this up.
https://github.com/dancinnamon-okta/swa_opp_demo
