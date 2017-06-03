package main

import (
	"crypto"
	"crypto/rsa"
	"crypto/sha256"
	"crypto/x509"
	"encoding/json"
	"encoding/pem"
	"errors"
	"fmt"
	"strconv"

	"github.com/hyperledger/fabric/core/chaincode/shim"
)

type Recipient struct {
	ID   string
	Name string
}

type AddRecipientRequest struct {
	Rp        Recipient
	PubKeyPem string
}

type AddIssuerRequest struct {
	Issuer    string
	PubKeyPem string
}

type Cert struct {
	Issuer      string
	Link        string
	Hash        string
	Description string
	Recipient   Recipient
}

type CertListElem struct {
	CertID  string
	Visible bool
}

type CertListResponseElem struct {
	CertID  string
	Cert    Cert
	Visible bool
}

type CertList []CertListElem

type ChangeVisibilityRequest struct {
	Rp      Recipient
	CertID  string
	Visible bool
}

type Chaincode struct {
}

func (t *Chaincode) Init(stub shim.ChaincodeStubInterface, function string, args []string) ([]byte, error) {
	stub.PutState("#Counter#", []byte{0})
	return []byte{}, nil
}

func addIssuer(stub shim.ChaincodeStubInterface, req AddIssuerRequest) {
	issuer_id := fmt.Sprintf("%s##%s", "ISSUER_PUB", req.Issuer)
	stub.PutState(issuer_id, []byte(req.PubKeyPem))
}

func addRecipient(stub shim.ChaincodeStubInterface, req AddRecipientRequest) {
	rp_id := fmt.Sprintf("%s##%s##%s", "RECIP_PUB", req.Rp.Name, req.Rp.ID)
	rp_list_id := fmt.Sprintf("%s##%s##%s", "RECIP_LIST", req.Rp.Name, req.Rp.ID)
	stub.PutState(rp_id, []byte(req.PubKeyPem))

	// Add an empty list to this uesr
	empty, _ := json.Marshal(CertList{})
	stub.PutState(rp_list_id, empty)
}

func recipientToPub(stub shim.ChaincodeStubInterface, rp Recipient) (rsa.PublicKey, error) {
	rp_id := fmt.Sprintf("%s##%s##%s", "RECIP_PUB", rp.Name, rp.ID)
	pub_pem, err := stub.GetState(rp_id)
	data, _ := pem.Decode([]byte(pub_pem))
	pub, _ := x509.ParsePKIXPublicKey(data.Bytes)

	return *pub.(*rsa.PublicKey), err
}

func issuerToPub(stub shim.ChaincodeStubInterface, issuer string) (rsa.PublicKey, error) {
	issuer_id := fmt.Sprintf("%s##%s", "ISSUER_PUB", issuer)
	pub_pem, err := stub.GetState(issuer_id)
	data, _ := pem.Decode([]byte(pub_pem))
	pub, _ := x509.ParsePKIXPublicKey(data.Bytes)

	return *pub.(*rsa.PublicKey), err
}

func idToCert(stub shim.ChaincodeStubInterface, ID string) (Cert, error) {
	cert_ID_id := fmt.Sprintf("%s##%s", "CERT", ID)
	data, err := stub.GetState(cert_ID_id)
	cert := Cert{}
	json.Unmarshal(data, &cert)

	return cert, err
}

func issueCert(stub shim.ChaincodeStubInterface, cert Cert) string {
	data, _ := json.Marshal(cert)
	cnt, _ := stub.GetState("#Counter#")
	curr_ID, _ := strconv.Atoi(string(cnt))
	cert_ID := fmt.Sprintf("%016x", curr_ID)
	cert_ID_id := fmt.Sprintf("%s##%s", "CERT", cert_ID)

	stub.PutState(cert_ID_id, data)
	addCertToRecipient(stub, cert.Recipient, cert_ID)

	return cert_ID
}

func getCertListByRecipient(stub shim.ChaincodeStubInterface, rp Recipient) CertList {
	var cert_list CertList
	rp_list_id := fmt.Sprintf("%s##%s##%s", "RECIP_LIST", rp.Name, rp.ID)
	old_json, _ := stub.GetState(rp_list_id)
	json.Unmarshal(old_json, &cert_list)

	return cert_list
}

func addCertToRecipient(stub shim.ChaincodeStubInterface, rp Recipient, cert_ID string) {
	rp_list_id := fmt.Sprintf("%s##%s##%s", "RECIP_LIST", rp.Name, rp.ID)
	cert_list := getCertListByRecipient(stub, rp)
	cert_list = append(cert_list, CertListElem{cert_ID, false})
	new_json, _ := json.Marshal(cert_list)
	stub.PutState(rp_list_id, new_json)
}

func changeCertListElemVisibility(stub shim.ChaincodeStubInterface, rp Recipient, ID string, visible bool) {
	cert_list := getCertListByRecipient(stub, rp)
	for _, v := range cert_list {
		if v.CertID == ID {
			v.Visible = visible
		}
	}
}

func getFullCertListByRecipient(stub shim.ChaincodeStubInterface, rp Recipient) []CertListResponseElem {
	var full_cert_list []CertListResponseElem
	cert_list := getCertListByRecipient(stub, rp)
	for _, v := range cert_list {
		cert, _ := idToCert(stub, v.CertID)
		full_cert_list = append(full_cert_list, CertListResponseElem{
			CertID:  v.CertID,
			Cert:    cert,
			Visible: v.Visible,
		})

	}

	return full_cert_list
}

func (t *Chaincode) Invoke(stub shim.ChaincodeStubInterface, function string, args []string) ([]byte, error) {
	switch function {
	case "AddIssuer":
		if len(args) != 1 {
			return []byte{}, errors.New("AddIssuer: Wrong #args!")
		}

		var issuer AddIssuerRequest
		json.Unmarshal([]byte(args[0]), &issuer)
		addIssuer(stub, issuer)

		return []byte{}, nil

	case "IssueCert":
		if len(args) != 2 {
			return []byte{}, errors.New("IssueCert: Wrong #args!")
		}

		// Verify the cert using the public key of issuer
		var cert Cert
		if err := json.Unmarshal([]byte(args[0]), &cert); err != nil {
			return []byte{}, errors.New("IssueCert: Wrong cert Format!")
		}
		pubkey, err := issuerToPub(stub, cert.Issuer)
		if err != nil {
			return []byte{}, errors.New("IssueCert: No such issuer!")
		}

		hashed := sha256.Sum256([]byte(args[0]))
		if err := rsa.VerifyPKCS1v15(&pubkey, crypto.SHA256, hashed[:], []byte(args[1])); err != nil {
			return []byte{}, errors.New("IssueCert: Integrity check failed!")
		}

		cert_id := issueCert(stub, cert)
		json_resp := fmt.Sprintf("{\"ID\": \"%s\"}", cert_id)
		return []byte(json_resp), nil

	case "AddRecipient":
		if len(args) != 1 {
			return []byte{}, errors.New("AddRecipient: Wrong #args!")
		}

		var rp AddRecipientRequest
		if err := json.Unmarshal([]byte(args[0]), &rp); err != nil {
			return []byte{}, errors.New(fmt.Sprint("AddRecipient: ", err))
		}
		addRecipient(stub, rp)

		return []byte{}, nil
	case "ChangeVisibility":
		if len(args) != 2 {
			return []byte{}, errors.New("ChangeVisibility: Wrong #arg!")
		}

		var req ChangeVisibilityRequest
		if err := json.Unmarshal([]byte(args[0]), &req); err != nil {
			return []byte{}, errors.New("ChangeVisibility: Wrong #args!")
		}

		hashed := sha256.Sum256([]byte(args[0]))
		pubkey, err := recipientToPub(stub, req.Rp)
		if err != nil {
			return []byte{}, errors.New("ChangeVisibility: No such recipient!")
		}
		if err := rsa.VerifyPKCS1v15(&pubkey, crypto.SHA256, hashed[:], []byte(args[1])); err != nil {
			return []byte{}, errors.New("ChangeVisibility: Integrity check failed!")
		}

		return []byte{}, nil
	default:
		return []byte{}, errors.New("Invalid FunctionName")
	}

}

// Query callback representing the query of a chaincode
func (t *Chaincode) Query(stub shim.ChaincodeStubInterface, function string, args []string) ([]byte, error) {
	switch function {
	case "GetCertList":
		if len(args) != 1 {
			return []byte{}, errors.New("GetCertList: Wrong #args!")
		}

		// Encrypt the returned data
		var rp Recipient
		if err := json.Unmarshal([]byte(args[0]), &rp); err != nil {
			return []byte{}, errors.New("GetCertList: Wrong Recipient Format!")
		}
		//		pubkey, err := recipientToPub(stub, rp)
		//		if err != nil {
		//			return []byte{}, errors.New("GetCertList: No such recipient!")
		//		}

		full_cert_list := getFullCertListByRecipient(stub, rp)
		raw_json, _ := json.Marshal(full_cert_list)
		return raw_json, nil
		//		encrpyted_json, err := rsa.EncryptPKCS1v15(nil, &pubkey, raw_json)

		//		return encrpyted_json, err
	default:
		return []byte{}, errors.New("Invalid Function Name")
	}

}

func main() {
	err := shim.Start(new(Chaincode))
	if err != nil {
		fmt.Printf("Error starting Simple chaincode: %s", err)
	}
}
