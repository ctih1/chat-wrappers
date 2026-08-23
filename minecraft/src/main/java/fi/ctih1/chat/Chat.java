package fi.ctih1.chat;

import org.bukkit.entity.Player;
import org.bukkit.plugin.java.JavaPlugin;
import fi.ctih1.chat.MessageListener;

import javax.annotation.Nullable;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

public final class Chat extends JavaPlugin {
    static Chat instance;
    HashMap<UUID, String> playerMessageMap = new HashMap<UUID, String>();

    @Override
    public void onEnable() {
        instance = this;

        getServer().getPluginManager().registerEvents(new MessageListener(), this);
    }

    public static Chat getInstance() {
        if(instance == null) {
            instance = new Chat();
        }

        return instance;
    }

    @Override
    public void onDisable() {
        // Plugin shutdown logic
    }
}
