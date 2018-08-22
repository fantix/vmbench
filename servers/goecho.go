// Taken from https://gist.github.com/paulsmith/775764#file-echo-go

package main

import (
	"crypto/tls"
	"fmt"
	"net"
	"os"
	"strconv"
)

const PORT = 25000

const serverKey = `-----BEGIN PRIVATE KEY-----
MIICdwIBADANBgkqhkiG9w0BAQEFAASCAmEwggJdAgEAAoGBANtb0+YrKuxevGpm
LrjaUhZSgz6zFAmuGFmKmUbdjmfv9zSmmdsQIksK++jK0Be9LeZy20j6ahOfuVa0
ufEmPoP7Fy4hXegKZR9cCWcIe/A6H2xWF1IIJLRTLaU8ol/I7T+um5HD5AwAwNPP
USNU0Eegmvp+xxWu3NX2m1Veot85AgMBAAECgYA3ZdZ673X0oexFlq7AAmrutkHt
CL7LvwrpOiaBjhyTxTeSNWzvtQBkIU8DOI0bIazA4UreAFffwtvEuPmonDb3F+Iq
SMAu42XcGyVZEl+gHlTPU9XRX7nTOXVt+MlRRRxL6t9GkGfUAXI3XxJDXW3c0vBK
UL9xqD8cORXOfE06rQJBAP8mEX1ERkR64Ptsoe4281vjTlNfIbs7NMPkUnrn9N/Y
BLhjNIfQ3HFZG8BTMLfX7kCS9D593DW5tV4Z9BP/c6cCQQDcFzCcVArNh2JSywOQ
ZfTfRbJg/Z5Lt9Fkngv1meeGNPgIMLN8Sg679pAOOWmzdMO3V706rNPzSVMME7E5
oPIfAkEA8pDddarP5tCvTTgUpmTFbakm0KoTZm2+FzHcnA4jRh+XNTjTOv98Y6Ik
eO5d1ZnKXseWvkZncQgxfdnMqqpj5wJAcNq/RVne1DbYlwWchT2Si65MYmmJ8t+F
0mcsULqjOnEMwf5e+ptq5LzwbyrHZYq5FNk7ocufPv/ZQrcSSC+cFwJBAKvOJByS
x56qyGeZLOQlWS2JS3KJo59XuLFGqcbgN9Om9xFa41Yb4N9NvplFivsvZdw3m1Q/
SPIXQuT8RMPDVNQ=
-----END PRIVATE KEY-----
`

const serverCert = `-----BEGIN CERTIFICATE-----
MIICVDCCAb2gAwIBAgIJANfHOBkZr8JOMA0GCSqGSIb3DQEBBQUAMF8xCzAJBgNV
BAYTAlhZMRcwFQYDVQQHEw5DYXN0bGUgQW50aHJheDEjMCEGA1UEChMaUHl0aG9u
IFNvZnR3YXJlIEZvdW5kYXRpb24xEjAQBgNVBAMTCWxvY2FsaG9zdDAeFw0xMDEw
MDgyMzAxNTZaFw0yMDEwMDUyMzAxNTZaMF8xCzAJBgNVBAYTAlhZMRcwFQYDVQQH
Ew5DYXN0bGUgQW50aHJheDEjMCEGA1UEChMaUHl0aG9uIFNvZnR3YXJlIEZvdW5k
YXRpb24xEjAQBgNVBAMTCWxvY2FsaG9zdDCBnzANBgkqhkiG9w0BAQEFAAOBjQAw
gYkCgYEA21vT5isq7F68amYuuNpSFlKDPrMUCa4YWYqZRt2OZ+/3NKaZ2xAiSwr7
6MrQF70t5nLbSPpqE5+5VrS58SY+g/sXLiFd6AplH1wJZwh78DofbFYXUggktFMt
pTyiX8jtP66bkcPkDADA089RI1TQR6Ca+n7HFa7c1fabVV6i3zkCAwEAAaMYMBYw
FAYDVR0RBA0wC4IJbG9jYWxob3N0MA0GCSqGSIb3DQEBBQUAA4GBAHPctQBEQ4wd
BJ6+JcpIraopLn8BGhbjNWj40mmRqWB/NAWF6M5ne7KpGAu7tLeG4hb1zLaldK8G
lxy2GPSRF6LFS48dpEj2HbMv2nvv6xxalDMJ9+DicWgAKTQ6bcX2j3GUkCR0g/T1
CRlNBAAlvhKzO7Clpf9l0YKBEfraJByX
-----END CERTIFICATE-----
`

func main() {
    if len(os.Args) > 1 && os.Args[1] == "--ssl" {
        cer, err := tls.X509KeyPair([]byte(serverCert), []byte(serverKey))
        config := &tls.Config{Certificates: []tls.Certificate{cer}}
        server, err := tls.Listen("tcp", ":"+strconv.Itoa(PORT), config)
    } else {
        server, err := net.Listen("tcp", ":"+strconv.Itoa(PORT))
    }
	if server == nil {
		panic("couldn't start listening: " + err.Error())
	}
	i := 0
	for {
		client, err := server.Accept()
		if client == nil {
			fmt.Printf("couldn't accept: " + err.Error())
			continue
		}
		i++
		fmt.Printf("%d: %v <-> %v\n", i, client.LocalAddr(), client.RemoteAddr())
		go handleConn(client)
	}
}

func handleConn(client net.Conn) {
    defer client.Close()
	buf := make([]byte, 102400)
	for {
		reqLen, err := client.Read(buf)
		if err != nil {
			break
		}
		if reqLen > 0 {
			client.Write(buf[:reqLen])
		}
	}
}

