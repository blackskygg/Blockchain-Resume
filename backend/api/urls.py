apps = [

]

urls = [
    (r"/user/register", "user.UserRegisterHandler"),
    (r"/user/login", "user.UserLoginHandler"),
    (r"/user/getCertifates", "user.UserQueryCertifiedHandler"),
    (r"/issuer/login", "issuer.CompanyLoginHandler"),
    (r"/issuer/register", "issuer.CompanyRegisterHandler"),
    (r"/issuer/certs", "issuer.CompanyIssueCertifates")
]
