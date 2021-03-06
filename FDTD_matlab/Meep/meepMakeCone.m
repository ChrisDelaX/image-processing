% by Christian Delacroix (2014)

function str = meepMakeCone(dn,dC,dAx,dh,drBot,drTop)

str = ['(make cone ' ...
    '(material (make dielectric (index ' num2str(dn) ')))' ...
    '(center ' num2str(dC(1)) ' ' num2str(dC(2)) ' ' num2str(dC(3)) ')' ...
    '(axis ' num2str(dAx(1)) ' ' num2str(dAx(2)) ' ' num2str(dAx(3)) ')' ...
    '(height ' num2str(dh) ')' ...
    '(radius ' num2str(drBot) ')(radius2 ' num2str(drTop) '))\n'];
