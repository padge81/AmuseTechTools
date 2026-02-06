#python3 - << 'EOF'
import pykms

card = pykms.Card()
print("Card opened")

res = pykms.ResourceManager(card)
print("ResourceManager:", res)

print("\nAttributes of ResourceManager:")
print(dir(res))

print("\nCard attributes:")
print(dir(card))
EOF