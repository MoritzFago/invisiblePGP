package main

import (
	"fmt"
	"github.com/kardianos/osext"
	"github.com/spf13/viper"
	//	"os"
	//	"path/filepath"
	"github.com/moritzfago/invisiblePGP/imapd"
)

func main() {
	viper.SetConfigName("config")
	viper.SetConfigType("toml")
	//var dir, err = filepath.Abs(filepath.Dir(os.Args[0]))
	var configdir, err = osext.ExecutableFolder()
	viper.AddConfigPath(configdir)
	viper.AddConfigPath("$HOME/golang/src/github.com/moritzfago/invisiblePGP")
	err = viper.ReadInConfig()
	if err != nil {
		panic(fmt.Errorf("Fatal error config file: %s \n", err))
	}

	var proxy = imapd.NewIMAPProxy(viper.GetInt("imap.localport"), viper.GetString("imapserver.server"), viper.GetInt("imapserver.port"))
	proxy.Start()

}
